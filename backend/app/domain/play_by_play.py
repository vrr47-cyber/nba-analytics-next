from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

from backend.app.domain.canonical import SourceMetadata


class PlayEventType(StrEnum):
    GAME_START = "game_start"
    PERIOD_START = "period_start"
    MADE_FIELD_GOAL = "made_field_goal"
    MISSED_FIELD_GOAL = "missed_field_goal"
    FREE_THROW = "free_throw"
    REBOUND = "rebound"
    TURNOVER = "turnover"
    FOUL = "foul"
    SUBSTITUTION = "substitution"
    TIMEOUT = "timeout"
    JUMP_BALL = "jump_ball"
    PERIOD_END = "period_end"
    GAME_END = "game_end"


class ParticipantRole(StrEnum):
    SCORING_TEAM = "scoring_team"
    SHOOTING_TEAM = "shooting_team"
    SHOOTER = "shooter"
    REBOUNDER = "rebounder"
    REBOUND_TEAM = "rebound_team"
    COMMITTING_PLAYER = "committing_player"
    COMMITTING_TEAM = "committing_team"
    ENTERING_PLAYER = "entering_player"
    EXITING_PLAYER = "exiting_player"
    TIMEOUT_TEAM = "timeout_team"
    JUMP_BALL_PLAYER_ONE = "jump_ball_player_one"
    JUMP_BALL_PLAYER_TWO = "jump_ball_player_two"


class NormalizedEventParticipant(BaseModel):
    role: ParticipantRole
    team_external_id: str | None = None
    player_external_id: str | None = None

    @model_validator(mode="after")
    def exactly_one_identity(self) -> NormalizedEventParticipant:
        if (self.team_external_id is None) == (self.player_external_id is None):
            raise ValueError("event participant must identify exactly one team or player")
        return self


class NormalizedPlayByPlayEvent(BaseModel):
    source: SourceMetadata
    game_external_id: str = Field(min_length=1)
    provider_event_id: str = Field(min_length=1)
    sequence_number: int = Field(ge=0)
    period: int = Field(ge=1)
    clock_seconds_remaining: int = Field(ge=0)
    event_type: PlayEventType
    outcome: str | None = None
    points_value: int | None = Field(default=None, ge=0)
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    participants: tuple[NormalizedEventParticipant, ...] = ()


class NormalizedPlayByPlayPayload(BaseModel):
    game_external_id: str = Field(min_length=1)
    events: tuple[NormalizedPlayByPlayEvent, ...]
    complete_payload: bool = True
