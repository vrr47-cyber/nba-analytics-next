from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.api.dependencies import get_services
from backend.app.core.errors import ApplicationError
from backend.app.schemas.envelope import Scope
from backend.app.schemas.players import PlayerListResponse, PlayerRecentGamesResponse, PlayerResponse, PlayerSplitsResponse, PlayerTrendsResponse
from backend.app.services.application import AppServices
from backend.app.services.player_analytics import PlayerAnalyticsError, player_detail, player_summaries, recent_games, splits, trends

router = APIRouter(prefix="/api/v1/players", tags=["players"])


def _db(services: AppServices) -> Session:
    if services.engine is None:
        raise ApplicationError("database_unavailable", "The analytics database is unavailable.")
    return Session(services.engine)


def _scope(season: str | None, competition: str | None) -> Scope:
    return Scope(season=season, competition=competition)


@router.get("", response_model=PlayerListResponse)
def list_players(season: str | None = None, competition: str | None = None, team_id: UUID | None = None, position: str | None = None, search: str | None = None, minimum_games: int = Query(0, ge=0), minimum_minutes: float = Query(0, ge=0), sort: str = "name", sort_direction: str = Query("asc", pattern="^(asc|desc)$"), limit: int = Query(50, ge=1, le=100), services: AppServices = Depends(get_services)) -> PlayerListResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = player_summaries(session, season, competition, team_id, position, search, minimum_games, minimum_minutes, sort, sort_direction == "desc", limit)
    except PlayerAnalyticsError as exc:
        raise ApplicationError("invalid_player_query", str(exc)) from exc
    return PlayerListResponse(data=data, scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{player_id}", response_model=PlayerResponse)
def get_player(player_id: UUID, season: str | None = None, competition: str | None = None, team_id: UUID | None = None, services: AppServices = Depends(get_services)) -> PlayerResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = player_detail(session, player_id, season, competition, team_id)
    except PlayerAnalyticsError as exc:
        raise ApplicationError("player_not_found", str(exc)) from exc
    return PlayerResponse(data=data, scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{player_id}/recent-games", response_model=PlayerRecentGamesResponse)
def get_recent_games(player_id: UUID, season: str | None = None, competition: str | None = None, team_id: UUID | None = None, limit: int = Query(10, ge=1, le=25), services: AppServices = Depends(get_services)) -> PlayerRecentGamesResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = recent_games(session, player_id, season, competition, team_id, limit)
    except PlayerAnalyticsError as exc:
        raise ApplicationError("player_not_found", str(exc)) from exc
    return PlayerRecentGamesResponse(data=data, scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{player_id}/trends", response_model=PlayerTrendsResponse)
def get_trends(player_id: UUID, season: str | None = None, competition: str | None = None, team_id: UUID | None = None, services: AppServices = Depends(get_services)) -> PlayerTrendsResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = trends(session, player_id, season, competition, team_id)
    except PlayerAnalyticsError as exc:
        raise ApplicationError("player_not_found", str(exc)) from exc
    return PlayerTrendsResponse(data=data, scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)


@router.get("/{player_id}/splits", response_model=PlayerSplitsResponse)
def get_splits(player_id: UUID, season: str | None = None, competition: str | None = None, team_id: UUID | None = None, services: AppServices = Depends(get_services)) -> PlayerSplitsResponse:
    try:
        with _db(services) as session:
            data, coverage, publication, provenance = splits(session, player_id, season, competition, team_id)
    except PlayerAnalyticsError as exc:
        raise ApplicationError("player_not_found", str(exc)) from exc
    return PlayerSplitsResponse(data=data, scope=_scope(season, competition), coverage=coverage, provenance=provenance, publication=publication)
