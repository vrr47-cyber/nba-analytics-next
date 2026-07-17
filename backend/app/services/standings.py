from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, Game, Season, SourceRun, Team, TeamGameStats
from backend.app.domain.coverage import Coverage
from backend.app.domain.publication import PublicationDecision
from backend.app.schemas.envelope import Provenance
from backend.app.schemas.standings import StandingRow, StandingsData
from backend.app.schemas.teams import TeamMetrics
from backend.app.services.team_analytics import _aggregate_map


class StandingsError(ValueError):
    pass


def _standings_sort_key(row: StandingRow) -> tuple[float, int, int, int, str, str]:
    return (-(row.win_percentage or 0), -row.wins, -row.point_differential, -row.points_for, row.team_name, str(row.team_id))


def _power_sort_key(row: StandingRow) -> tuple[bool, float, int, float, int, str, str]:
    return (row.power_value is None, -(row.power_value or 0), -row.point_differential, -(row.win_percentage or 0), -row.wins, row.team_name, str(row.team_id))


def _scope(session: Session, season_code: str, competition_code: str) -> tuple[Season, Competition]:
    seasons = list(session.scalars(select(Season).where(Season.season_code == season_code)))
    if len(seasons) != 1:
        raise StandingsError(f"season scope is unavailable or ambiguous: {season_code}")
    competitions = list(session.scalars(select(Competition).where(Competition.league_id == seasons[0].league_id, Competition.code == competition_code)))
    if len(competitions) != 1:
        raise StandingsError(f"competition scope is unavailable or ambiguous: {competition_code}")
    return seasons[0], competitions[0]


def _eligible_games(session: Session, season: Season, competition: Competition) -> list[Game]:
    games = list(session.scalars(select(Game).where(Game.season_id == season.id, Game.competition_id == competition.id, Game.status == "final")))
    if any(game.home_final_score is None or game.away_final_score is None for game in games):
        raise StandingsError("eligible final games cannot have partial final scores")
    if any(game.home_team_id == game.away_team_id for game in games):
        raise StandingsError("eligible final games must have distinct teams")
    if any(game.home_final_score == game.away_final_score for game in games):
        raise StandingsError("tied final games are unsupported by the standings domain")
    for game in games:
        stats = list(session.scalars(select(TeamGameStats).where(TeamGameStats.game_id == game.id)))
        if stats and (len(stats) != 2 or {row.team_id for row in stats} != {game.home_team_id, game.away_team_id}):
            raise StandingsError(f"team-stat rows do not reconcile for game {game.id}")
        points = {row.team_id: row.points for row in stats}
        if stats and (points.get(game.home_team_id) != game.home_final_score or points.get(game.away_team_id) != game.away_final_score):
            raise StandingsError(f"team-stat points do not reconcile for game {game.id}")
    return games


def _synthetic(session: Session, games: list[Game]) -> bool:
    if not games:
        return False
    runs = [session.get(SourceRun, game.source_run_id) for game in games]
    return all(bool(run and (run.metadata_json or {}).get("synthetic")) for run in runs)


def derive_standings(session: Session, *, season_code: str | None, competition_code: str | None, view: str = "standings") -> tuple[StandingsData, Coverage, PublicationDecision, Provenance]:
    if not season_code or not competition_code:
        raise StandingsError("season and competition are required for a standings scope")
    if view not in {"standings", "power"}:
        raise StandingsError("view must be standings or power")
    season, competition = _scope(session, season_code, competition_code)
    games = _eligible_games(session, season, competition)
    teams = list(session.scalars(select(Team).where(Team.league_id == season.league_id, Team.active.is_(True)).order_by(Team.full_name)))
    records: dict[UUID, dict[str, Any]] = defaultdict(lambda: {"games_played": 0, "wins": 0, "losses": 0, "points_for": 0, "points_against": 0})
    for game in games:
        assert game.home_final_score is not None and game.away_final_score is not None
        home = records[game.home_team_id]
        away = records[game.away_team_id]
        home["games_played"] += 1
        away["games_played"] += 1
        home["points_for"] += game.home_final_score
        home["points_against"] += game.away_final_score
        away["points_for"] += game.away_final_score
        away["points_against"] += game.home_final_score
        if game.home_final_score > game.away_final_score:
            home["wins"] += 1
            away["losses"] += 1
        else:
            away["wins"] += 1
            home["losses"] += 1
    aggregates, _, _ = _aggregate_map(session, season_code, competition_code)
    rows: list[StandingRow] = []
    for team in teams:
        record = records[team.id]
        aggregate = aggregates.get(team.id)
        metrics = aggregate.metrics() if aggregate is not None else TeamMetrics()
        differential = record["points_for"] - record["points_against"]
        rows.append(StandingRow(team_id=team.id, team_name=team.full_name, abbreviation=team.abbreviation, conference=None, division=None, games_played=record["games_played"], wins=record["wins"], losses=record["losses"], win_percentage=record["wins"] / record["games_played"] if record["games_played"] else None, points_for=record["points_for"], points_against=record["points_against"], point_differential=differential, metrics=metrics, power_value=metrics.net_rating, power_basis="recorded_net_rating"))
    if view == "power":
        rows.sort(key=_power_sort_key)
        explanation = "Power Ordering (ordered by recorded Net Rating)"
    else:
        rows.sort(key=_standings_sort_key)
        explanation = "Recorded Standings (derived from eligible final recorded games)"
    synthetic = _synthetic(session, games)
    reason = "Synthetic recorded sample — not publishable." if synthetic else "Derived from final recorded games; expected competition population is not established."
    coverage = Coverage(included_games=len(games), expected_games=None, included_entities=len(rows), expected_entities=None, coverage_ratio=None, is_complete=False, is_publishable=False, reason=reason)
    publication = PublicationDecision.synthetic() if synthetic else PublicationDecision.from_coverage("unknown")
    run_ids = {game.source_run_id for game in games}
    updates = [game.source_updated_at for game in games if game.source_updated_at]
    provenance = Provenance(source="canonical-warehouse", source_updated_at=max(updates) if updates else None, ingested_at=datetime.now(timezone.utc), dataset_version="phase11-standings-v1", metric_version="team-analytics.v1", synthetic=synthetic, contributing_source_run_count=len(run_ids))
    return StandingsData(view=view, ordering_explanation=explanation, rows=rows), coverage, publication, provenance
