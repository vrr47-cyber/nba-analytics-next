from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_services
from backend.app.core.errors import ApplicationError
from backend.app.schemas.envelope import Scope
from backend.app.schemas.standings import PublicationDecision, StandingsResponse
from backend.app.services.application import AppServices
from backend.app.services.standings import StandingsError, derive_standings

router = APIRouter(prefix="/api/v1/standings", tags=["standings"])


def _db(services: AppServices) -> Session:
    if services.engine is None:
        raise ApplicationError("database_unavailable", "The analytics database is unavailable.")
    return Session(services.engine)


@router.get("", response_model=StandingsResponse)
def get_standings(season: str | None = None, competition: str | None = None, view: str = Query("standings", pattern="^(standings|power)$"), services: AppServices = Depends(get_services)) -> StandingsResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = derive_standings(session, season_code=season, competition_code=competition, view=view)
    except StandingsError as exc:
        raise ApplicationError("invalid_standings_query", str(exc)) from exc
    return StandingsResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=PublicationDecision.model_validate(publication.model_dump()))
