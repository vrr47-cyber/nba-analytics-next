from __future__ import annotations

import re
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator, model_validator

SEASON_PATTERN = re.compile(r"^\d{4}-\d{2}$")


class CompetitionCode(StrEnum):
    REGULAR = "regular"
    PLAYOFFS = "playoffs"
    PRESEASON = "preseason"
    SUMMER_LEAGUE = "summer_league"


class SeasonStatus(StrEnum):
    UPCOMING = "upcoming"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ARCHIVED = "archived"


class GameStatus(StrEnum):
    SCHEDULED = "scheduled"
    FINAL = "final"
    POSTPONED = "postponed"
    CANCELLED = "cancelled"


class ParticipationStatus(StrEnum):
    PLAYED = "played"
    DID_NOT_PLAY = "did_not_play"
    INACTIVE = "inactive"
    NOT_WITH_TEAM = "not_with_team"
    UNKNOWN = "unknown"


class CompletenessState(StrEnum):
    UNKNOWN = "unknown"
    EMPTY = "empty"
    PARTIAL = "partial"
    COMPLETE = "complete"
    INCONSISTENT = "inconsistent"
    STALE = "stale"
    FAILED_VALIDATION = "failed_validation"


def validate_season_code(value: str) -> str:
    if not SEASON_PATTERN.fullmatch(value):
        raise ValueError("season must use YYYY-YY format, for example 2024-25")
    if int(value[5:]) != (int(value[:4]) + 1) % 100:
        raise ValueError("season must contain consecutive season years")
    return value


class SourceMetadata(BaseModel):
    provider: str = Field(min_length=1)
    external_id: str = Field(min_length=1)
    source_updated_at: str | None = None
    retrieved_at: str
    schema_fingerprint: str | None = None


class NormalizedLeague(BaseModel):
    source: SourceMetadata
    code: str = Field(min_length=1)
    display_name: str = Field(min_length=1)


class NormalizedSeason(BaseModel):
    source: SourceMetadata
    league_code: str = Field(min_length=1)
    season: str
    display_label: str = Field(min_length=1)
    status: SeasonStatus
    is_current: bool = False

    _season = field_validator("season")(validate_season_code)


class NormalizedCompetition(BaseModel):
    source: SourceMetadata
    league_code: str = Field(min_length=1)
    code: CompetitionCode
    display_name: str = Field(min_length=1)
    category: str = Field(min_length=1)


class NormalizedTeam(BaseModel):
    source: SourceMetadata
    league_code: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    short_name: str = Field(min_length=1)
    abbreviation: str = Field(min_length=1, max_length=8)
    city: str | None = None


class NormalizedPlayer(BaseModel):
    source: SourceMetadata
    slug: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    active: bool = True
    birth_date: str | None = None


class NormalizedRosterEntry(BaseModel):
    source: SourceMetadata
    season: str
    competition_code: CompetitionCode
    team_external_id: str
    player_external_id: str
    snapshot_at: str
    jersey_number: str | None = None
    listed_position: str | None = None
    roster_status: str | None = None

    _season = field_validator("season")(validate_season_code)


class NormalizedGame(BaseModel):
    source: SourceMetadata
    season: str
    competition_code: CompetitionCode
    scheduled_start: str
    game_date: str
    home_team_external_id: str
    away_team_external_id: str
    status: GameStatus
    home_final_score: int | None = Field(default=None, ge=0)
    away_final_score: int | None = Field(default=None, ge=0)
    neutral_site: bool = False
    official_external_url: str | None = None
    archival_external_url: str | None = None

    _season = field_validator("season")(validate_season_code)

    @field_validator("away_team_external_id")
    @classmethod
    def distinct_teams(cls, value: str, info):
        if value == info.data.get("home_team_external_id"):
            raise ValueError("home and away teams must differ")
        return value

    @model_validator(mode="after")
    def final_scores_together(self):
        if self.status == GameStatus.FINAL and (self.home_final_score is None or self.away_final_score is None):
            raise ValueError("final games require both final scores")
        return self


class BoxScoreLine(BaseModel):
    points: int = Field(ge=0)
    field_goals_made: int = Field(ge=0)
    field_goals_attempted: int = Field(ge=0)
    three_pointers_made: int = Field(ge=0)
    three_pointers_attempted: int = Field(ge=0)
    free_throws_made: int = Field(ge=0)
    free_throws_attempted: int = Field(ge=0)
    offensive_rebounds: int = Field(ge=0)
    defensive_rebounds: int = Field(ge=0)
    total_rebounds: int = Field(ge=0)
    assists: int = Field(ge=0)
    steals: int = Field(ge=0)
    blocks: int = Field(ge=0)
    turnovers: int = Field(ge=0)
    personal_fouls: int = Field(ge=0)
    plus_minus: int | None = None

    @model_validator(mode="after")
    def made_not_over_attempted(self):
        for made, attempted in ((self.field_goals_made, self.field_goals_attempted), (self.three_pointers_made, self.three_pointers_attempted), (self.free_throws_made, self.free_throws_attempted)):
            if made > attempted:
                raise ValueError("made values cannot exceed attempts")
        return self


class NormalizedTeamGameStats(BoxScoreLine):
    source: SourceMetadata
    game_external_id: str
    team_external_id: str
    opponent_external_id: str
    home_away: str
    result: str
    minutes: str


class NormalizedPlayerGameStats(BoxScoreLine):
    source: SourceMetadata
    game_external_id: str
    player_external_id: str
    team_external_id: str
    starter: bool | None = None
    participation_status: ParticipationStatus
    status_comment: str | None = None
    minutes: str | None = None


class NormalizedStandingsRow(BaseModel):
    source: SourceMetadata
    season: str
    competition_code: CompetitionCode
    team_external_id: str
    observed_at: str
    wins: int = Field(ge=0)
    losses: int = Field(ge=0)
    conference_rank: int | None = Field(default=None, ge=1)
    league_rank: int | None = Field(default=None, ge=1)

    _season = field_validator("season")(validate_season_code)
