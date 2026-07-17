from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_services
from backend.app.core.errors import ApplicationError
from backend.app.schemas.envelope import Scope
from backend.app.schemas.shots import PlayerShotProfile, PlayerShotResponse, ShotAnalyticsSummary, ShotSummaryResponse, ShotZonesResponse
from backend.app.services.application import AppServices
from backend.app.services.shots import shot_summary

router = APIRouter(prefix="/api/v1/shots", tags=["shots"])


def _db(services: AppServices) -> Session:
    if services.engine is None:
        raise ApplicationError("database_unavailable", "The analytics database is unavailable.")
    return Session(services.engine)


def _scope(season: str | None, competition: str | None) -> Scope:
    return Scope(season=season, competition=competition)


def _summary_response(summary: dict, coverage, publication, provenance, season: str | None, competition: str | None) -> ShotSummaryResponse:
    return ShotSummaryResponse(data=ShotAnalyticsSummary.model_validate(summary), scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/summary", response_model=ShotSummaryResponse)
def get_summary(season: str | None = None, competition: str | None = None, team_id: UUID | None = None, services: AppServices = Depends(get_services)) -> ShotSummaryResponse:
    with _db(services) as session:
        summary, coverage, publication, provenance = shot_summary(session, season=season, competition=competition, team_id=team_id)
    return _summary_response(summary, coverage, publication, provenance, season, competition)


@router.get("/players/{player_id}", response_model=PlayerShotResponse)
def get_player_shots(player_id: UUID, season: str | None = None, competition: str | None = None, services: AppServices = Depends(get_services)) -> PlayerShotResponse:
    with _db(services) as session:
        summary, coverage, publication, provenance = shot_summary(session, season=season, competition=competition, player_id=player_id)
    return PlayerShotResponse(data=PlayerShotProfile(player_id=player_id, summary=ShotAnalyticsSummary.model_validate(summary)), scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/zones", response_model=ShotZonesResponse)
def get_zones(season: str | None = None, competition: str | None = None, player_id: UUID | None = None, team_id: UUID | None = None, services: AppServices = Depends(get_services)) -> ShotZonesResponse:
    with _db(services) as session:
        summary, coverage, publication, provenance = shot_summary(session, season=season, competition=competition, player_id=player_id, team_id=team_id)
    return ShotZonesResponse(data=summary["zone_distribution"], scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)
