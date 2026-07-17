from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from backend.app.schemas.envelope import Envelope
from backend.app.schemas.teams import PublicationDecision


class ShotDistribution(BaseModel):
    key: str
    attempts: int
    share: float | None = None


class ShotCoordinate(BaseModel):
    x: float
    y: float
    result: str
    shot_type: str


class ShotAnalyticsSummary(BaseModel):
    attempts: int
    makes: int
    field_goal_attempts: int
    field_goal_makes: int
    three_point_attempts: int
    three_point_makes: int
    fg_percentage: float | None = None
    three_point_percentage: float | None = None
    effective_fg_percentage: float | None = None
    actual_points: int
    average_distance: float | None = None
    expected_fg_percentage: float | None = None
    expected_points: float | None = None
    zone_distribution: list[ShotDistribution]
    shot_type_distribution: list[ShotDistribution]
    coordinates: list[ShotCoordinate]


class ShotSummaryResponse(Envelope[ShotAnalyticsSummary]):
    publication: PublicationDecision


class PlayerShotProfile(BaseModel):
    player_id: UUID
    summary: ShotAnalyticsSummary


class PlayerShotResponse(Envelope[PlayerShotProfile]):
    publication: PublicationDecision


class ShotZonesResponse(Envelope[list[ShotDistribution]]):
    publication: PublicationDecision
