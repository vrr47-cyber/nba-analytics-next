from __future__ import annotations

from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from backend.app.schemas.envelope import Envelope


class PublicationDecision(BaseModel):
    publishable: bool
    code: str
    reason: str


class TeamAttribution(BaseModel):
    state: str
    team_ids: list[UUID] = Field(default_factory=list)
    team_names: list[str] = Field(default_factory=list)


class PlayerMetrics(BaseModel):
    games_available: int = 0
    games_played: int = 0
    games_started: int | None = None
    non_participation_count: int = 0
    total_minutes: float = 0
    minutes_per_game: float | None = None
    points: int = 0
    rebounds: int = 0
    assists: int = 0
    steals: int = 0
    blocks: int = 0
    turnovers: int = 0
    fouls: int = 0
    points_per_game: float | None = None
    rebounds_per_game: float | None = None
    assists_per_game: float | None = None
    steals_per_game: float | None = None
    blocks_per_game: float | None = None
    field_goal_percentage: float | None = None
    three_point_percentage: float | None = None
    free_throw_percentage: float | None = None
    effective_fg_percentage: float | None = None
    true_shooting_percentage: float | None = None
    points_per_36: float | None = None
    rebounds_per_36: float | None = None
    assists_per_36: float | None = None
    steals_per_36: float | None = None
    blocks_per_36: float | None = None
    three_point_attempt_rate: float | None = None
    free_throw_rate: float | None = None


class PlayerSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    position: str | None = None
    current_team_id: UUID | None = None
    current_team_name: str | None = None
    team_attribution: TeamAttribution
    metrics: PlayerMetrics


class PlayerDetail(PlayerSummary):
    methodology_path: str = "/methodology/player-metrics"


class PlayerRecentGame(BaseModel):
    game_id: UUID
    date: date
    team_id: UUID
    team_name: str
    opponent_id: UUID
    opponent_name: str
    home_away: str
    result: str
    participation_status: str
    status_comment: str | None = None
    starter: bool | None = None
    minutes: float | None = None
    points: int | None = None
    rebounds: int | None = None
    assists: int | None = None
    steals: int | None = None
    blocks: int | None = None
    turnovers: int | None = None
    fouls: int | None = None
    field_goals_made: int | None = None
    field_goals_attempted: int | None = None
    three_pointers_made: int | None = None
    three_pointers_attempted: int | None = None
    free_throws_made: int | None = None
    free_throws_attempted: int | None = None


class PlayerTrendPoint(BaseModel):
    game_id: UUID
    date: date
    minutes: float | None = None
    points: int | None = None
    rebounds: int | None = None
    assists: int | None = None
    true_shooting_percentage: float | None = None
    rolling_points_per_game: float | None = None
    sample_size: int


class PlayerSplit(BaseModel):
    split: str
    sample_size: int
    metrics: PlayerMetrics


class PlayerResponse(Envelope[PlayerDetail]):
    publication: PublicationDecision


class PlayerListResponse(Envelope[list[PlayerSummary]]):
    publication: PublicationDecision


class PlayerRecentGamesResponse(Envelope[list[PlayerRecentGame]]):
    publication: PublicationDecision


class PlayerTrendsResponse(Envelope[list[PlayerTrendPoint]]):
    publication: PublicationDecision


class PlayerSplitsResponse(Envelope[list[PlayerSplit]]):
    publication: PublicationDecision
