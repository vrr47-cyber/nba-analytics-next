from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_services
from backend.app.core.errors import ApplicationError
from backend.app.schemas.envelope import Scope
from backend.app.schemas.teams import RecentGamesResponse, RosterResponse, TeamListResponse, TeamResponse, TrendsResponse
from backend.app.services.application import AppServices
from backend.app.services.team_analytics import TeamAnalyticsError, recent_games, roster, team_detail, team_summaries, trends

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])


def _db(services: AppServices) -> Session:
    if services.engine is None:
        raise ApplicationError("database_unavailable", "The analytics database is unavailable.")
    return Session(services.engine)


@router.get("", response_model=TeamListResponse)
def list_teams(season: str | None = None, competition: str | None = None, conference: str | None = None, search: str | None = None, sort: str = "name", sort_direction: str = Query("asc", pattern="^(asc|desc)$"), services: AppServices = Depends(get_services)) -> TeamListResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = team_summaries(session, season, competition, search, conference, sort, sort_direction == "desc")
    except TeamAnalyticsError as exc:
        raise ApplicationError("invalid_team_query", str(exc)) from exc
    return TeamListResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=publication)


def _detail_response(team_id: UUID, services: AppServices, season: str | None, competition: str | None) -> TeamResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = team_detail(session, team_id, season, competition)
    except TeamAnalyticsError as exc:
        raise ApplicationError("team_not_found", str(exc)) from exc
    return TeamResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(team_id: UUID, season: str | None = None, competition: str | None = None, services: AppServices = Depends(get_services)) -> TeamResponse:
    return _detail_response(team_id, services, season, competition)


@router.get("/{team_id}/roster", response_model=RosterResponse)
def get_roster(team_id: UUID, season: str | None = None, competition: str | None = None, services: AppServices = Depends(get_services)) -> RosterResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = roster(session, team_id, season, competition)
    except TeamAnalyticsError as exc:
        raise ApplicationError("team_not_found", str(exc)) from exc
    return RosterResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{team_id}/recent-games", response_model=RecentGamesResponse)
def get_recent_games(team_id: UUID, season: str | None = None, competition: str | None = None, limit: int = Query(10, ge=1, le=25), services: AppServices = Depends(get_services)) -> RecentGamesResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = recent_games(session, team_id, season, competition, limit)
    except TeamAnalyticsError as exc:
        raise ApplicationError("team_not_found", str(exc)) from exc
    return RecentGamesResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{team_id}/trends", response_model=TrendsResponse)
def get_trends(team_id: UUID, season: str | None = None, competition: str | None = None, services: AppServices = Depends(get_services)) -> TrendsResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = trends(session, team_id, season, competition)
    except TeamAnalyticsError as exc:
        raise ApplicationError("team_not_found", str(exc)) from exc
    return TrendsResponse(data=data, scope=Scope(season=season, competition=competition), coverage=coverage, provenance=provenance, publication=publication)
