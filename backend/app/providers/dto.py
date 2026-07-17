from datetime import date, datetime

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


class FixturePlayerDTO(BaseModel):
    provider_player_id: str = Field(min_length=1)
    slug: str = Field(min_length=1)
    full_name: str = Field(min_length=1)
    first_name: str | None = None
    last_name: str | None = None
    position: str | None = None
    active: bool = True
    birth_date: date | None = None


class FixturePlayersDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    revision: str
    loaded_at: datetime
    players: tuple[FixturePlayerDTO, ...]


class FixtureRosterDTO(BaseModel):
    provider_roster_id: str = Field(min_length=1)
    provider_team_id: str = Field(min_length=1)
    provider_player_id: str = Field(min_length=1)
    season: str
    competition_code: str
    snapshot_at: datetime
    roster_status: str | None = None
    jersey_number: str | None = None
    listed_position: str | None = None


class FixtureRostersDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    revision: str
    loaded_at: datetime
    rosters: tuple[FixtureRosterDTO, ...]
