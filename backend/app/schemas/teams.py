from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from backend.app.domain.coverage import Coverage
from backend.app.schemas.envelope import Envelope, Provenance


class PublicationDecision(BaseModel):
    publishable: bool
    code: str
    reason: str


class TeamMetrics(BaseModel):
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    home_wins: int = 0
    home_losses: int = 0
    away_wins: int = 0
    away_losses: int = 0
    last_10_wins: int = 0
    last_10_losses: int = 0
    last_10_sample_size: int = 0
    points_scored: int = 0
    points_allowed: int = 0
    offensive_rating: float | None = None
    defensive_rating: float | None = None
    net_rating: float | None = None
    pace: float | None = None
    effective_fg_percentage: float | None = None
    true_shooting_percentage: float | None = None
    turnover_percentage: float | None = None
    offensive_rebound_percentage: float | None = None
    free_throw_rate: float | None = None
    conference_rank: int | None = None


class TeamSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    abbreviation: str
    conference: str | None = None
    metrics: TeamMetrics


class TeamDetail(TeamSummary):
    city: str | None = None
    methodology_path: str = "/methodology/team-metrics"


class RosterEntry(BaseModel):
    player_id: UUID
    name: str
    position: str | None = None
    jersey_number: str | None = None
    roster_status: str | None = None
    games: int = 0
    minutes: float | None = None
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    true_shooting_percentage: float | None = None


class RecentGame(BaseModel):
    game_id: UUID
    date: date
    opponent_id: UUID
    opponent_name: str
    home_away: str
    result: str
    team_points: int
    opponent_points: int
    competition: str
    official_external_url: str | None = None
    archival_external_url: str | None = None


class TrendPoint(BaseModel):
    game_id: UUID
    date: date
    net_rating: float | None = None
    offensive_rating: float | None = None
    defensive_rating: float | None = None
    pace: float | None = None
    cumulative_wins: int
    cumulative_losses: int
    sample_size: int


class TeamCoverage(BaseModel):
    coverage: Coverage
    publication: PublicationDecision
    provenance: Provenance


class TeamResponse(Envelope[TeamDetail]):
    publication: PublicationDecision


class TeamListResponse(Envelope[list[TeamSummary]]):
    publication: PublicationDecision


class RosterResponse(Envelope[list[RosterEntry]]):
    publication: PublicationDecision


class RecentGamesResponse(Envelope[list[RecentGame]]):
    publication: PublicationDecision


class TrendsResponse(Envelope[list[TrendPoint]]):
    publication: PublicationDecision


class MetricMetadata(BaseModel):
    id: str
    label: str
    formula: str
    unit: str
    version: str
    direction: str
    estimated: bool
    null_behavior: str
