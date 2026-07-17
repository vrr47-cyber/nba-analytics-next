from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_services
from backend.app.core.errors import ApplicationError
from backend.app.schemas.envelope import Scope
from backend.app.schemas.explore import ExploreResponse
from backend.app.services.application import AppServices
from backend.app.services.explore import ExploreError, build_explore

router = APIRouter(prefix="/api/v1/explore", tags=["explore"])


def _db(services: AppServices) -> Session:
    if services.engine is None:
        raise ApplicationError("database_unavailable", "The analytics database is unavailable.")
    return Session(services.engine)


@router.get("", response_model=ExploreResponse)
def explore(season: str | None = None, competition: str | None = None, featured_team_limit: int = Query(4, ge=1, le=10), featured_player_limit: int = Query(5, ge=1, le=10), recent_game_limit: int = Query(5, ge=1, le=10), services: AppServices = Depends(get_services)) -> ExploreResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = build_explore(session, season, competition, featured_team_limit, featured_player_limit, recent_game_limit)
    except ExploreError as exc:
        raise ApplicationError("invalid_explore_query", str(exc)) from exc
    return ExploreResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=publication)
