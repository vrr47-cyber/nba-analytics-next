from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, Game, Player, PlayerGameStats, RosterSnapshot, Season, SourceRun, Team, TeamGameStats
from backend.app.domain.coverage import Coverage
from backend.app.domain.metrics import METRIC_VERSION, estimated_possessions, ratio
from backend.app.schemas.envelope import Provenance
from backend.app.schemas.teams import PublicationDecision, RecentGame, RosterEntry, TeamDetail, TeamMetrics, TeamSummary, TrendPoint


class TeamAnalyticsError(ValueError):
    pass


@dataclass
class _Aggregate:
    games: list[tuple[Game, TeamGameStats, TeamGameStats]]

    def metrics(self) -> TeamMetrics:
        rows = self.games
        points = sum(team.points for _, team, _ in rows)
        allowed = sum(opponent.points for _, _, opponent in rows)
        fga = sum(team.field_goals_attempted for _, team, _ in rows)
        fta = sum(team.free_throws_attempted for _, team, _ in rows)
        orb = sum(team.offensive_rebounds for _, team, _ in rows)
        turnovers = sum(team.turnovers for _, team, _ in rows)
        opp_drb = sum(opponent.defensive_rebounds for _, _, opponent in rows)
        possessions = sum(estimated_possessions(team.field_goals_attempted, team.free_throws_attempted, team.offensive_rebounds, team.turnovers) for _, team, _ in rows)
        opponent_possessions = sum(estimated_possessions(opponent.field_goals_attempted, opponent.free_throws_attempted, opponent.offensive_rebounds, opponent.turnovers) for _, _, opponent in rows)
        three_made = sum(team.three_pointers_made for _, team, _ in rows)
        made = sum(team.field_goals_made for _, team, _ in rows)
        home = [item for item in rows if item[1].home_away == "home"]
        away = [item for item in rows if item[1].home_away == "away"]
        wins = sum(team.points > opponent.points for _, team, opponent in rows)
        last = sorted(rows, key=lambda item: (item[0].scheduled_start, str(item[0].id)), reverse=True)[:10]
        last_wins = sum(team.points > opponent.points for _, team, opponent in last)
        duration = sum(48.0 for _ in rows)
        game_possessions = (possessions + opponent_possessions) / 2
        offensive_rating = ratio(100 * points, possessions)
        defensive_rating = ratio(100 * allowed, opponent_possessions)
        return TeamMetrics(
            games_played=len(rows), wins=wins, losses=len(rows) - wins,
            home_wins=sum(team.points > opponent.points for _, team, opponent in home),
            home_losses=len(home) - sum(team.points > opponent.points for _, team, opponent in home),
            away_wins=sum(team.points > opponent.points for _, team, opponent in rows if team.home_away == "away"),
            away_losses=len(away) - sum(team.points > opponent.points for _, team, opponent in rows if team.home_away == "away"),
            last_10_wins=last_wins, last_10_losses=len(last) - last_wins, last_10_sample_size=len(last),
            points_scored=points, points_allowed=allowed,
            offensive_rating=offensive_rating, defensive_rating=defensive_rating,
            net_rating=offensive_rating - defensive_rating if offensive_rating is not None and defensive_rating is not None else None,
            pace=ratio(48 * game_possessions, duration / 48) if duration > 0 else None,
            effective_fg_percentage=ratio(made + 0.5 * three_made, fga),
            true_shooting_percentage=ratio(points, 2 * (fga + 0.44 * fta)),
            turnover_percentage=ratio(turnovers, fga + 0.44 * fta + turnovers),
            offensive_rebound_percentage=ratio(orb, orb + opp_drb),
            free_throw_rate=ratio(fta, fga),
        )


def _scope(session: Session, season_code: str | None, competition_code: str | None) -> tuple[Season | None, Competition | None]:
    season = session.scalar(select(Season).where(Season.season_code == season_code)) if season_code else None
    competition = session.scalar(select(Competition).where(Competition.code == competition_code)) if competition_code else None
    return season, competition


def _aggregate_map(session: Session, season_code: str | None, competition_code: str | None) -> tuple[dict[UUID, _Aggregate], Season | None, Competition | None]:
    season, competition = _scope(session, season_code, competition_code)
    query = select(Game, TeamGameStats).join(TeamGameStats, TeamGameStats.game_id == Game.id).where(Game.status == "final")
    if season:
        query = query.where(Game.season_id == season.id)
    if competition:
        query = query.where(Game.competition_id == competition.id)
    grouped: dict[UUID, dict[UUID, tuple[Game, TeamGameStats]]] = defaultdict(dict)
    for game, stats in session.execute(query):
        grouped[game.id][stats.team_id] = (game, stats)
    aggregates: dict[UUID, _Aggregate] = {}
    for game_rows in grouped.values():
        if len(game_rows) != 2:
            continue
        game = next(iter(game_rows.values()))[0]
        for team_id, (_, stats) in game_rows.items():
            opponent = next(row[1] for other_id, row in game_rows.items() if other_id != team_id)
            aggregates.setdefault(team_id, _Aggregate([])).games.append((game, stats, opponent))
    return aggregates, season, competition


def _rows(session: Session, team_id: UUID, season_code: str | None, competition_code: str | None) -> tuple[Team, _Aggregate, Season | None, Competition | None]:
    team = session.get(Team, team_id)
    if team is None:
        raise TeamAnalyticsError("Team was not found.")
    aggregates, season, competition = _aggregate_map(session, season_code, competition_code)
    return team, aggregates.get(team_id, _Aggregate([])), season, competition


def _synthetic_for(session: Session, aggregate: _Aggregate) -> bool:
    source_run_ids = {game.source_run_id for game, _, _ in aggregate.games}
    runs = [session.get(SourceRun, source_run_id) for source_run_id in source_run_ids]
    return bool(runs) and all(bool(run and (run.metadata_json or {}).get("synthetic")) for run in runs)


def coverage_for(team: Team, aggregate: _Aggregate, synthetic: bool = False) -> tuple[Coverage, PublicationDecision, Provenance]:
    count = len(aggregate.games)
    reason = "Synthetic recorded sample — not publishable." if synthetic else ("No eligible final games." if count == 0 else "Recorded sample is partial.")
    coverage = Coverage(included_games=count, expected_games=None, included_entities=1, expected_entities=None, coverage_ratio=None, is_complete=False, is_publishable=False, reason=reason)
    publication = PublicationDecision(publishable=False, code="synthetic_fixture" if synthetic else "blocked_partial_coverage", reason=reason)
    updates = [game.source_updated_at for game, _, _ in aggregate.games if game.source_updated_at]
    return coverage, publication, Provenance(source="canonical-warehouse", source_updated_at=max(updates) if updates else None, ingested_at=datetime.now(timezone.utc), metric_version=METRIC_VERSION, synthetic=synthetic, contributing_source_run_count=len({game.source_run_id for game, _, _ in aggregate.games}))


def team_summaries(session: Session, season_code: str | None, competition_code: str | None, search: str | None, conference: str | None, sort: str, descending: bool) -> tuple[list[TeamSummary], Coverage, PublicationDecision, Provenance]:
    teams = list(session.scalars(select(Team).where(Team.active.is_(True)).order_by(Team.full_name)))
    if search:
        needle = search.casefold()
        teams = [team for team in teams if needle in team.full_name.casefold() or needle in team.abbreviation.casefold()]
    if conference:
        teams = [team for team in teams if team.conference == conference]
    results: list[TeamSummary] = []
    coverages = []
    provenances = []
    aggregates, _, _ = _aggregate_map(session, season_code, competition_code)
    source_runs = {run.id: run for run in session.scalars(select(SourceRun))}
    for team in teams:
        aggregate = aggregates.get(team.id, _Aggregate([]))
        synthetic = bool(aggregate.games) and all(bool(source_runs.get(game.source_run_id) and (source_runs[game.source_run_id].metadata_json or {}).get("synthetic")) for game, _, _ in aggregate.games)
        coverage, publication, provenance = coverage_for(team, aggregate, synthetic)
        results.append(TeamSummary(id=team.id, name=team.full_name, abbreviation=team.abbreviation, conference=team.conference, metrics=aggregate.metrics()))
        coverages.append(coverage)
        provenances.append(provenance)
    valid_sort = {"name", "offensive_rating", "defensive_rating", "net_rating", "pace", "effective_fg_percentage"}
    if sort not in valid_sort:
        raise TeamAnalyticsError("Unsupported team sort field.")
    def key(item: TeamSummary):
        value = item.name if sort == "name" else getattr(item.metrics, sort)
        return (value is None, value if value is not None else 0, item.name, str(item.id))
    results.sort(key=key, reverse=descending)
    reason = "Synthetic recorded sample — not publishable." if results else "No teams match the requested scope."
    return results, Coverage(included_games=sum(c.included_games for c in coverages), included_entities=len(results), reason=reason), PublicationDecision(publishable=False, code="synthetic_fixture", reason=reason), Provenance(source="canonical-warehouse", metric_version=METRIC_VERSION, synthetic=True, contributing_source_run_count=sum(p.contributing_source_run_count or 0 for p in provenances))


def team_detail(session: Session, team_id: UUID, season_code: str | None, competition_code: str | None) -> tuple[TeamDetail, Coverage, PublicationDecision, Provenance]:
    team, aggregate, _, _ = _rows(session, team_id, season_code, competition_code)
    coverage, publication, provenance = coverage_for(team, aggregate, _synthetic_for(session, aggregate))
    return TeamDetail(id=team.id, name=team.full_name, abbreviation=team.abbreviation, conference=team.conference, city=team.city, metrics=aggregate.metrics()), coverage, publication, provenance


def recent_games(session: Session, team_id: UUID, season_code: str | None, competition_code: str | None, limit: int) -> tuple[list[RecentGame], Coverage, PublicationDecision, Provenance]:
    team, aggregate, _, _ = _rows(session, team_id, season_code, competition_code)
    games = sorted(aggregate.games, key=lambda item: (item[0].scheduled_start, str(item[0].id)), reverse=True)[:limit]
    data = []
    for game, stats, opponent in games:
        opponent_id = opponent.team_id
        opponent_team = session.get(Team, opponent_id)
        data.append(RecentGame(game_id=game.id, date=game.game_date, opponent_id=opponent_id, opponent_name=opponent_team.full_name if opponent_team else "Unavailable", home_away=stats.home_away, result="W" if stats.points > opponent.points else "L", team_points=stats.points, opponent_points=opponent.points, competition=competition_code or "recorded", official_external_url=game.official_external_url, archival_external_url=game.archival_external_url))
    return data, *coverage_for(team, aggregate, _synthetic_for(session, aggregate))


def trends(session: Session, team_id: UUID, season_code: str | None, competition_code: str | None) -> tuple[list[TrendPoint], Coverage, PublicationDecision, Provenance]:
    team, aggregate, _, _ = _rows(session, team_id, season_code, competition_code)
    ordered = sorted(aggregate.games, key=lambda item: (item[0].scheduled_start, str(item[0].id)))
    points = []
    wins = losses = 0
    for index in range(len(ordered)):
        window = ordered[max(0, index - 9): index + 1]
        current = _Aggregate(window).metrics()
        wins += ordered[index][1].points > ordered[index][2].points
        losses += ordered[index][1].points <= ordered[index][2].points
        points.append(TrendPoint(game_id=ordered[index][0].id, date=ordered[index][0].game_date, net_rating=current.net_rating, offensive_rating=current.offensive_rating, defensive_rating=current.defensive_rating, pace=current.pace, cumulative_wins=wins, cumulative_losses=losses, sample_size=len(window)))
    return points, *coverage_for(team, aggregate, _synthetic_for(session, aggregate))


def roster(session: Session, team_id: UUID, season_code: str | None, competition_code: str | None) -> tuple[list[RosterEntry], Coverage, PublicationDecision, Provenance]:
    team, aggregate, season, competition = _rows(session, team_id, season_code, competition_code)
    if season is None:
        return [], *coverage_for(team, aggregate, _synthetic_for(session, aggregate))
    snapshot_query = select(RosterSnapshot).where(RosterSnapshot.team_id == team_id, RosterSnapshot.season_id == season.id, RosterSnapshot.snapshot_at <= datetime.combine(date.max, datetime.min.time(), tzinfo=timezone.utc))
    if competition:
        snapshot_query = snapshot_query.where(RosterSnapshot.competition_id == competition.id)
    snapshots = list(session.scalars(snapshot_query.order_by(RosterSnapshot.snapshot_at.desc())))
    latest: dict[UUID, RosterSnapshot] = {}
    for snapshot in snapshots:
        latest.setdefault(snapshot.player_id, snapshot)
    game_ids = {game.id for game, _, _ in aggregate.games}
    stats = list(session.scalars(select(PlayerGameStats).where(PlayerGameStats.team_id == team_id, PlayerGameStats.game_id.in_(game_ids)))) if game_ids else []
    by_player: dict[UUID, list[PlayerGameStats]] = defaultdict(list)
    for row in stats:
        by_player[row.player_id].append(row)
    data = []
    for player_id, snapshot in latest.items():
        player = session.get(Player, player_id)
        rows = by_player[player_id]
        if player is None:
            continue
        minutes = sum(float(row.minutes.split(":")[0]) + float(row.minutes.split(":")[1]) / 60 for row in rows if row.minutes)
        points = sum(row.points for row in rows)
        fga = sum(row.field_goals_attempted for row in rows)
        fta = sum(row.free_throws_attempted for row in rows)
        data.append(RosterEntry(player_id=player.id, name=player.full_name, position=snapshot.listed_position, jersey_number=snapshot.jersey_number, roster_status=snapshot.roster_status, games=len(rows), minutes=minutes, points=points, rebounds=sum(row.total_rebounds for row in rows), assists=sum(row.assists for row in rows), true_shooting_percentage=ratio(points, 2 * (fga + 0.44 * fta))))
    return data, *coverage_for(team, aggregate, _synthetic_for(session, aggregate))
