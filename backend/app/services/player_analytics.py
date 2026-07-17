from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, Game, Player, PlayerGameStats, RosterSnapshot, Season, SourceRun, Team
from backend.app.domain.canonical import ParticipationStatus
from backend.app.domain.coverage import Coverage
from backend.app.domain.metrics import ratio
from backend.app.schemas.envelope import Provenance
from backend.app.schemas.players import PlayerDetail, PlayerMetrics, PlayerRecentGame, PlayerSplit, PlayerSummary, PlayerTrendPoint, PublicationDecision, TeamAttribution


class PlayerAnalyticsError(ValueError):
    pass


KNOWN_POSITIONS = {"PG", "SG", "SF", "PF", "C", "G", "F", "G-F", "F-C", "UNKNOWN"}
PLAYER_METRIC_VERSION = "player-analytics.v1"


@dataclass(frozen=True)
class _PlayerRow:
    stats: PlayerGameStats
    game: Game
    team: Team


@dataclass
class _PlayerAggregate:
    player: Player
    rows: list[_PlayerRow]
    current_team_id: UUID | None
    current_team_name: str | None
    current_team_state: str
    team_names: dict[UUID, str]

    @property
    def played(self) -> list[_PlayerRow]:
        return [row for row in self.rows if row.stats.participation_status == ParticipationStatus.PLAYED]

    @property
    def games_available(self) -> int:
        return len({row.game.id for row in self.rows})

    def metrics(self, rows: list[_PlayerRow] | None = None) -> PlayerMetrics:
        source_rows = self.rows if rows is None else rows
        selected = self.played if rows is None else [row for row in rows if row.stats.participation_status == ParticipationStatus.PLAYED]
        games_played = len({row.game.id for row in selected})
        games_started: int | None = None
        if selected and all(row.stats.starter is not None for row in selected):
            games_started = sum(bool(row.stats.starter) for row in selected)
        def total(field: str) -> int:
            return sum(int(getattr(row.stats, field)) for row in selected)
        minutes = sum(_minutes(row.stats.minutes) for row in selected)
        points, rebounds, assists = total("points"), total("total_rebounds"), total("assists")
        fgm, fga = total("field_goals_made"), total("field_goals_attempted")
        tpm, tpa = total("three_pointers_made"), total("three_pointers_attempted")
        ftm, fta = total("free_throws_made"), total("free_throws_attempted")
        def per_game(value: float) -> float | None:
            return ratio(value, games_played)

        def per_36(value: float) -> float | None:
            return ratio(value * 36, minutes)
        return PlayerMetrics(
            games_available=len({row.game.id for row in source_rows}), games_played=games_played,
            games_started=games_started, non_participation_count=len(source_rows) - len(selected),
            total_minutes=minutes, minutes_per_game=per_game(minutes), points=points, rebounds=rebounds,
            assists=assists, steals=total("steals"), blocks=total("blocks"), turnovers=total("turnovers"),
            fouls=total("personal_fouls"), points_per_game=per_game(points), rebounds_per_game=per_game(rebounds),
            assists_per_game=per_game(assists), steals_per_game=per_game(total("steals")), blocks_per_game=per_game(total("blocks")),
            field_goal_percentage=ratio(fgm, fga), three_point_percentage=ratio(tpm, tpa), free_throw_percentage=ratio(ftm, fta),
            effective_fg_percentage=ratio(fgm + 0.5 * tpm, fga), true_shooting_percentage=ratio(points, 2 * (fga + 0.44 * fta)),
            points_per_36=per_36(points), rebounds_per_36=per_36(rebounds), assists_per_36=per_36(assists),
            steals_per_36=per_36(total("steals")), blocks_per_36=per_36(total("blocks")),
            three_point_attempt_rate=ratio(tpa, fga), free_throw_rate=ratio(fta, fga),
        )

    def attribution(self) -> TeamAttribution:
        ids = list(self.team_names)
        return TeamAttribution(state="multiple_teams" if len(ids) > 1 else ("single_team" if ids else "unavailable"), team_ids=ids, team_names=[self.team_names[team_id] for team_id in ids])


def _minutes(value: str | None) -> float:
    if value is None:
        raise PlayerAnalyticsError("played player stat row is missing minutes")
    try:
        minute, second = value.split(":")
        parsed = float(minute) + float(second) / 60
    except (ValueError, TypeError) as exc:
        raise PlayerAnalyticsError(f"invalid player minutes value: {value}") from exc
    if parsed <= 0:
        raise PlayerAnalyticsError("played player stat row must have positive minutes")
    return parsed


def _team_won(game: Game, team_id: UUID) -> bool:
    if game.home_final_score is None or game.away_final_score is None:
        raise PlayerAnalyticsError(f"final game {game.id} is missing canonical scores")
    return (team_id == game.home_team_id and game.home_final_score > game.away_final_score) or (team_id == game.away_team_id and game.away_final_score > game.home_final_score)


def _scope(session: Session, season_code: str | None, competition_code: str | None) -> tuple[Season | None, Competition | None]:
    season = session.scalar(select(Season).where(Season.season_code == season_code)) if season_code else None
    competition = session.scalar(select(Competition).where(Competition.code == competition_code)) if competition_code else None
    return season, competition


def _load(session: Session, season_code: str | None, competition_code: str | None, team_id: UUID | None) -> tuple[dict[UUID, _PlayerAggregate], dict[UUID, Team], Season | None, Competition | None]:
    season, competition = _scope(session, season_code, competition_code)
    if team_id is not None and session.get(Team, team_id) is None:
        raise PlayerAnalyticsError("team filter was not found")
    query = select(PlayerGameStats, Game, Player, Team).join(Game, Game.id == PlayerGameStats.game_id).join(Player, Player.id == PlayerGameStats.player_id).join(Team, Team.id == PlayerGameStats.team_id).where(Game.status == "final")
    if season:
        query = query.where(Game.season_id == season.id)
    if competition:
        query = query.where(Game.competition_id == competition.id)
    if team_id:
        query = query.where(PlayerGameStats.team_id == team_id)
    rows_by_player: dict[UUID, list[_PlayerRow]] = defaultdict(list)
    players: dict[UUID, Player] = {}
    teams: dict[UUID, Team] = {team.id: team for team in session.scalars(select(Team))}
    seen: set[tuple[UUID, UUID]] = set()
    for stats, game, player, team in session.execute(query):
        key = (player.id, game.id)
        if key in seen:
            raise PlayerAnalyticsError(f"duplicate logical player appearance for player {player.id} and game {game.id}")
        seen.add(key)
        if stats.participation_status == ParticipationStatus.PLAYED:
            _minutes(stats.minutes)
        players[player.id] = player
        rows_by_player[player.id].append(_PlayerRow(stats, game, team))
    scope_end = season.end_date if season and season.end_date else date.max
    snapshot_query = select(RosterSnapshot).where(RosterSnapshot.snapshot_at <= datetime.combine(scope_end, time.max, tzinfo=timezone.utc))
    if season:
        snapshot_query = snapshot_query.where(RosterSnapshot.season_id == season.id)
    if competition:
        snapshot_query = snapshot_query.where(RosterSnapshot.competition_id == competition.id)
    latest: dict[UUID, list[RosterSnapshot]] = defaultdict(list)
    for snapshot in session.scalars(snapshot_query.order_by(RosterSnapshot.snapshot_at.desc())):
        if not latest[snapshot.player_id] or latest[snapshot.player_id][0].snapshot_at == snapshot.snapshot_at:
            latest[snapshot.player_id].append(snapshot)
    aggregates: dict[UUID, _PlayerAggregate] = {}
    for player_id, rows in rows_by_player.items():
        team_names = {row.team.id: row.team.full_name for row in rows}
        snapshots = latest.get(player_id, [])
        current_ids = {snapshot.team_id for snapshot in snapshots}
        current_id = next(iter(current_ids)) if len(current_ids) == 1 else None
        current_name = teams[current_id].full_name if current_id and current_id in teams else None
        aggregates[player_id] = _PlayerAggregate(players[player_id], rows, current_id, current_name, "multiple_teams" if len(current_ids) > 1 else ("single_team" if current_id else "unavailable"), team_names)
    return aggregates, teams, season, competition


def _provenance(session: Session, rows: list[_PlayerRow]) -> tuple[Coverage, PublicationDecision, Provenance]:
    source_ids = {row.stats.source_run_id for row in rows}
    sources = [session.get(SourceRun, source_id) for source_id in source_ids]
    synthetic = bool(sources) and all(bool(source and (source.metadata_json or {}).get("synthetic")) for source in sources)
    games = len({row.game.id for row in rows})
    if not rows:
        reason, code = "No eligible player observations are available.", "blocked_missing_data"
    elif synthetic:
        reason, code = "Synthetic recorded sample — not publishable.", "synthetic_fixture"
    else:
        reason, code = "Recorded player sample is partial.", "blocked_partial_coverage"
    updates = [row.stats.source_updated_at for row in rows if row.stats.source_updated_at]
    coverage = Coverage(included_games=games, included_entities=1, reason=reason)
    publication = PublicationDecision(publishable=False, code=code, reason=reason)
    return coverage, publication, Provenance(source="canonical-warehouse", source_updated_at=max(updates) if updates else None, ingested_at=datetime.now(timezone.utc), metric_version=PLAYER_METRIC_VERSION, synthetic=synthetic, contributing_source_run_count=len(source_ids))


def _summary(aggregate: _PlayerAggregate) -> PlayerSummary:
    return PlayerSummary(id=aggregate.player.id, name=aggregate.player.full_name, position=aggregate.player.position, current_team_id=aggregate.current_team_id, current_team_name=aggregate.current_team_name, team_attribution=aggregate.attribution(), metrics=aggregate.metrics())


def player_summaries(session: Session, season_code: str | None, competition_code: str | None, team_id: UUID | None, position: str | None, search: str | None, minimum_games: int, minimum_minutes: float, sort: str, descending: bool, limit: int) -> tuple[list[PlayerSummary], Coverage, PublicationDecision, Provenance]:
    if position is not None:
        position = position.upper()
        if position not in KNOWN_POSITIONS:
            raise PlayerAnalyticsError("unsupported canonical player position")
    if limit < 1 or limit > 100:
        raise PlayerAnalyticsError("player directory limit must be between 1 and 100")
    aggregates, _, _, _ = _load(session, season_code, competition_code, team_id)
    summaries = [_summary(aggregate) for aggregate in aggregates.values() if (not position or (aggregate.player.position or "UNKNOWN").upper() == position) and (not search or search.casefold() in aggregate.player.full_name.casefold())]
    summaries = [summary for summary in summaries if summary.metrics.games_played >= minimum_games and (summary.metrics.total_minutes or 0) >= minimum_minutes]
    sort_fields = {"name", "games_played", "minutes_per_game", "points_per_game", "rebounds_per_game", "assists_per_game", "true_shooting_percentage"}
    if sort not in sort_fields:
        raise PlayerAnalyticsError("unsupported player sort field")
    def key(summary: PlayerSummary):
        value = summary.name if sort == "name" else getattr(summary.metrics, sort)
        return (value is None, value if value is not None else 0, summary.name, str(summary.id))
    summaries.sort(key=key, reverse=descending)
    summaries = summaries[:limit]
    rows = [row for aggregate in aggregates.values() for row in aggregate.rows]
    coverage, publication, provenance = _provenance(session, rows)
    coverage.included_entities = len(summaries)
    return summaries, coverage, publication, provenance


def player_detail(session: Session, player_id: UUID, season_code: str | None, competition_code: str | None, team_id: UUID | None) -> tuple[PlayerDetail, Coverage, PublicationDecision, Provenance]:
    aggregates, _, _, _ = _load(session, season_code, competition_code, team_id)
    aggregate = aggregates.get(player_id)
    if aggregate is None:
        raise PlayerAnalyticsError("player was not found in the requested scope")
    coverage, publication, provenance = _provenance(session, aggregate.rows)
    summary = _summary(aggregate)
    return PlayerDetail(**summary.model_dump(), methodology_path="/methodology/player-metrics"), coverage, publication, provenance


def recent_games(session: Session, player_id: UUID, season_code: str | None, competition_code: str | None, team_id: UUID | None, limit: int) -> tuple[list[PlayerRecentGame], Coverage, PublicationDecision, Provenance]:
    aggregates, teams, _, _ = _load(session, season_code, competition_code, team_id)
    aggregate = aggregates.get(player_id)
    if aggregate is None:
        raise PlayerAnalyticsError("player was not found in the requested scope")
    data: list[PlayerRecentGame] = []
    for row in sorted(aggregate.rows, key=lambda item: (item.game.scheduled_start, str(item.game.id)), reverse=True)[:limit]:
        opponent_id = row.game.away_team_id if row.team.id == row.game.home_team_id else row.game.home_team_id
        opponent = teams.get(opponent_id)
        stats = row.stats
        played = stats.participation_status == ParticipationStatus.PLAYED
        data.append(PlayerRecentGame(game_id=row.game.id, date=row.game.game_date, team_id=row.team.id, team_name=row.team.full_name, opponent_id=opponent_id, opponent_name=opponent.full_name if opponent else "Unavailable", home_away="home" if row.team.id == row.game.home_team_id else "away", result="W" if _team_won(row.game, row.team.id) else "L", participation_status=stats.participation_status, status_comment=stats.status_comment, starter=stats.starter, minutes=_minutes(stats.minutes) if played else None, points=stats.points if played else None, rebounds=stats.total_rebounds if played else None, assists=stats.assists if played else None, steals=stats.steals if played else None, blocks=stats.blocks if played else None, turnovers=stats.turnovers if played else None, fouls=stats.personal_fouls if played else None, field_goals_made=stats.field_goals_made if played else None, field_goals_attempted=stats.field_goals_attempted if played else None, three_pointers_made=stats.three_pointers_made if played else None, three_pointers_attempted=stats.three_pointers_attempted if played else None, free_throws_made=stats.free_throws_made if played else None, free_throws_attempted=stats.free_throws_attempted if played else None))
    return data, *_provenance(session, aggregate.rows)


def trends(session: Session, player_id: UUID, season_code: str | None, competition_code: str | None, team_id: UUID | None) -> tuple[list[PlayerTrendPoint], Coverage, PublicationDecision, Provenance]:
    aggregates, _, _, _ = _load(session, season_code, competition_code, team_id)
    aggregate = aggregates.get(player_id)
    if aggregate is None:
        raise PlayerAnalyticsError("player was not found in the requested scope")
    ordered = sorted(aggregate.played, key=lambda item: (item.game.scheduled_start, str(item.game.id)))
    data: list[PlayerTrendPoint] = []
    for index, row in enumerate(ordered):
        window = ordered[max(0, index - 4): index + 1]
        window_metrics = aggregate.metrics(window)
        data.append(PlayerTrendPoint(game_id=row.game.id, date=row.game.game_date, minutes=_minutes(row.stats.minutes), points=row.stats.points, rebounds=row.stats.total_rebounds, assists=row.stats.assists, true_shooting_percentage=window_metrics.true_shooting_percentage, rolling_points_per_game=window_metrics.points_per_game, sample_size=window_metrics.games_played))
    return data, *_provenance(session, aggregate.rows)


def splits(session: Session, player_id: UUID, season_code: str | None, competition_code: str | None, team_id: UUID | None) -> tuple[list[PlayerSplit], Coverage, PublicationDecision, Provenance]:
    aggregates, _, _, _ = _load(session, season_code, competition_code, team_id)
    aggregate = aggregates.get(player_id)
    if aggregate is None:
        raise PlayerAnalyticsError("player was not found in the requested scope")
    ordered = sorted(aggregate.played, key=lambda item: (item.game.scheduled_start, str(item.game.id)), reverse=True)
    groups = {"home": [row for row in aggregate.played if row.team.id == row.game.home_team_id], "away": [row for row in aggregate.played if row.team.id == row.game.away_team_id], "wins": [row for row in aggregate.played if _team_won(row.game, row.team.id)], "losses": [row for row in aggregate.played if not _team_won(row.game, row.team.id)], "last_5": ordered[:5], "last_10": ordered[:10], "full_recorded_sample": aggregate.played}
    data = [PlayerSplit(split=name, sample_size=len(rows), metrics=aggregate.metrics(rows)) for name, rows in groups.items()]
    return data, *_provenance(session, aggregate.rows)
