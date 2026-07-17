from __future__ import annotations

from datetime import date
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel

from backend.app.domain.coverage import Coverage
from backend.app.schemas.envelope import Envelope, Provenance
from backend.app.schemas.players import PlayerSummary
from backend.app.schemas.teams import TeamSummary

T = TypeVar("T")


class PublicationDecision(BaseModel):
    publishable: bool
    code: str
    reason: str


class ExploreSection(BaseModel, Generic[T]):
    data: T
    coverage: Coverage
    publication: PublicationDecision
    provenance: Provenance


class ExploreRecentGame(BaseModel):
    game_id: UUID
    date: date
    home_team_id: UUID
    home_team_name: str
    away_team_id: UUID
    away_team_name: str
    home_final_score: int
    away_final_score: int
    status: str
    competition: str
    coverage_state: str


class ExploreCoverageSummary(BaseModel):
    teams: Coverage
    players: Coverage
    recent_games: Coverage


class ExploreData(BaseModel):
    featured_teams: ExploreSection[list[TeamSummary]]
    featured_players: ExploreSection[list[PlayerSummary]]
    recent_games: ExploreSection[list[ExploreRecentGame]]
    coverage_summary: ExploreCoverageSummary


class ExploreResponse(Envelope[ExploreData]):
    publication: PublicationDecision
