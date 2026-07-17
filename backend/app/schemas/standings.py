from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from backend.app.schemas.envelope import Envelope
from backend.app.schemas.teams import PublicationDecision, TeamMetrics


class StandingRow(BaseModel):
    team_id: UUID
    team_name: str
    abbreviation: str
    conference: str | None = None
    division: str | None = None
    games_played: int
    wins: int
    losses: int
    win_percentage: float | None = None
    points_for: int
    points_against: int
    point_differential: int
    metrics: TeamMetrics
    power_value: float | None = None
    power_basis: str = "recorded_net_rating"


class StandingsData(BaseModel):
    view: str
    ordering_explanation: str
    rows: list[StandingRow]


class StandingsResponse(Envelope[StandingsData]):
    publication: PublicationDecision
