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


class FixtureGameDTO(BaseModel):
    provider_game_id: str = Field(min_length=1)
    season: str
    competition_code: str
    home_provider_team_id: str = Field(min_length=1)
    away_provider_team_id: str = Field(min_length=1)
    scheduled_start: datetime
    status: str
    neutral_site: bool = False
    home_final_score: int | None = Field(default=None, ge=0)
    away_final_score: int | None = Field(default=None, ge=0)
    official_external_url: str | None = None
    archival_external_url: str | None = None


class FixtureGamesDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    revision: str
    loaded_at: datetime
    games: tuple[FixtureGameDTO, ...]


class FixtureTeamStatDTO(BaseModel):
    provider_team_id: str = Field(min_length=1)
    opponent_provider_team_id: str = Field(min_length=1)
    home_away: str
    result: str
    minutes: str
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


class FixturePlayerStatDTO(FixtureTeamStatDTO):
    provider_player_id: str = Field(min_length=1)
    starter: bool | None = None
    participation_status: str
    status_comment: str | None = None
    player_minutes: str | None = None


class FixtureBoxScoreDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    revision: str
    loaded_at: datetime
    provider_game_id: str = Field(min_length=1)
    complete_roster_coverage: bool = True
    team_stats: tuple[FixtureTeamStatDTO, ...]
    player_stats: tuple[FixturePlayerStatDTO, ...]


class FixtureEventParticipantDTO(BaseModel):
    role: str
    provider_team_id: str | None = None
    provider_player_id: str | None = None


class FixturePlayByPlayEventDTO(BaseModel):
    provider_event_id: str = Field(min_length=1)
    sequence_number: int = Field(ge=0)
    period: int = Field(ge=1)
    clock_seconds_remaining: int = Field(ge=0)
    event_type: str
    outcome: str | None = None
    points_value: int | None = Field(default=None, ge=0)
    home_score: int = Field(ge=0)
    away_score: int = Field(ge=0)
    participants: tuple[FixtureEventParticipantDTO, ...] = ()


class FixturePlayByPlayDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    revision: str
    loaded_at: datetime
    provider_game_id: str = Field(min_length=1)
    complete_payload: bool = True
    events: tuple[FixturePlayByPlayEventDTO, ...]


class FixtureShotDTO(BaseModel):
    provider_shot_id: str = Field(min_length=1)
    provider_game_id: str = Field(min_length=1)
    provider_team_id: str = Field(min_length=1)
    provider_player_id: str = Field(min_length=1)
    period: int = Field(ge=1)
    clock: str = Field(min_length=1)
    sequence_number: int | None = Field(default=None, ge=0)
    provider_x: float | None = None
    provider_y: float | None = None
    shot_distance: float | None = Field(default=None, ge=0)
    zone_code: str = Field(min_length=1)
    shot_type: str = Field(min_length=1)
    result: str = Field(min_length=1)
    point_value: int = Field(ge=0, le=3)


class FixtureShotsDTO(BaseModel):
    provider: str = "fixture"
    schema_version: str
    revision: str
    loaded_at: datetime
    provider_game_id: str = Field(min_length=1)
    complete_payload: bool = True
    shots: tuple[FixtureShotDTO, ...]
