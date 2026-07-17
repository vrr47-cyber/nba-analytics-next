from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from backend.app.database.models import Competition, Game, Season, SourceRun, Team
from backend.app.domain.coverage import Coverage
from backend.app.schemas.envelope import Provenance
from backend.app.schemas.explore import ExploreCoverageSummary, ExploreData, ExploreRecentGame, ExploreSection, PublicationDecision as ExplorePublicationDecision
from backend.app.services.player_analytics import player_summaries
from backend.app.services.team_analytics import team_summaries


class ExploreError(ValueError):
    pass


def _scope(session: Session, season_code: str | None, competition_code: str | None) -> tuple[Season | None, Competition | None]:
    season = session.scalar(select(Season).where(Season.season_code == season_code)) if season_code else None
    competition = session.scalar(select(Competition).where(Competition.code == competition_code)) if competition_code else None
    return season, competition


def _recent_games(session: Session, season_code: str | None, competition_code: str | None, limit: int) -> ExploreSection[list[ExploreRecentGame]]:
    season, competition = _scope(session, season_code, competition_code)
    # SQLAlchemy requires explicit aliases when the same table is joined twice.
    home = aliased(Team, name="explore_home")
    away = aliased(Team, name="explore_away")
    query = select(Game, home, away, Competition).join(home, home.id == Game.home_team_id).join(away, away.id == Game.away_team_id).join(Competition, Competition.id == Game.competition_id).where(Game.status == "final")
    if season:
        query = query.where(Game.season_id == season.id)
    if competition:
        query = query.where(Game.competition_id == competition.id)
    rows = list(session.execute(query.order_by(Game.scheduled_start.desc(), Game.id.desc()).limit(limit)))
    data = [ExploreRecentGame(game_id=game.id, date=game.game_date, home_team_id=home_row.id, home_team_name=home_row.full_name, away_team_id=away_row.id, away_team_name=away_row.full_name, home_final_score=game.home_final_score, away_final_score=game.away_final_score, status=game.status, competition=competition_row.code, coverage_state="synthetic" if _source_is_synthetic(session, game.source_run_id) else "recorded") for game, home_row, away_row, competition_row in rows]
    synthetic = bool(data) and all(item.coverage_state == "synthetic" for item in data)
    reason = "Synthetic recorded sample — not publishable." if synthetic else ("No completed games are available." if not data else "Recorded sample is partial.")
    coverage = Coverage(included_games=len(data), included_entities=len(data), reason=reason)
    publication = ExplorePublicationDecision(publishable=False, code="synthetic_fixture" if synthetic else ("blocked_missing_data" if not data else "blocked_partial_coverage"), reason=reason)
    provenance = Provenance(source="canonical-warehouse", ingested_at=datetime.now(timezone.utc), synthetic=synthetic, contributing_source_run_count=len({game.source_run_id for game, *_ in rows}))
    return ExploreSection(data=data, coverage=coverage, publication=publication, provenance=provenance)


def _source_is_synthetic(session: Session, source_run_id: UUID) -> bool:
    run = session.get(SourceRun, source_run_id)
    return bool(run and (run.metadata_json or {}).get("synthetic"))


def build_explore(session: Session, season_code: str | None, competition_code: str | None, featured_team_limit: int, featured_player_limit: int, recent_game_limit: int) -> tuple[ExploreData, Coverage, ExplorePublicationDecision, Provenance]:
    if not 1 <= featured_team_limit <= 10 or not 1 <= featured_player_limit <= 10 or not 1 <= recent_game_limit <= 10:
        raise ExploreError("Explore section limits must be between 1 and 10")
    teams, team_coverage, team_publication, team_provenance = team_summaries(session, season_code, competition_code, None, None, "name", False, featured_team_limit)
    players, player_coverage, player_publication, player_provenance = player_summaries(session, season_code, competition_code, None, None, None, 0, 0, "name", False, featured_player_limit)
    games = _recent_games(session, season_code, competition_code, recent_game_limit)
    data = ExploreData(featured_teams=ExploreSection(data=teams, coverage=team_coverage, publication=ExplorePublicationDecision.model_validate(team_publication.model_dump()), provenance=team_provenance), featured_players=ExploreSection(data=players, coverage=player_coverage, publication=ExplorePublicationDecision.model_validate(player_publication.model_dump()), provenance=player_provenance), recent_games=games, coverage_summary=ExploreCoverageSummary(teams=team_coverage, players=player_coverage, recent_games=games.coverage))
    synthetic = team_provenance.synthetic or player_provenance.synthetic or games.provenance.synthetic
    reason = "Synthetic recorded sample — not publishable." if synthetic else "Explore contains a recorded sample that is not publication-complete."
    coverage = Coverage(included_games=games.coverage.included_games, included_entities=team_coverage.included_entities + player_coverage.included_entities, reason=reason)
    publication = ExplorePublicationDecision(publishable=False, code="synthetic_fixture" if synthetic else "blocked_partial_coverage", reason=reason)
    provenance = Provenance(source="composed-canonical-warehouse", ingested_at=datetime.now(timezone.utc), synthetic=synthetic, contributing_source_run_count=None)
    return data, coverage, publication, provenance
