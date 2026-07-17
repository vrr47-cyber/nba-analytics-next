from datetime import datetime

from pydantic import BaseModel, Field


class FixtureTeamDTO(BaseModel):
    provider_team_id: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    short_name: str = Field(min_length=1)
    abbreviation: str = Field(min_length=1, max_length=8)
    city: str | None = None


class FixtureTeamsDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    provider_league_id: str
    league_code: str
    league_name: str
    loaded_at: datetime
    teams: tuple[FixtureTeamDTO, ...]
