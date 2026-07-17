from pydantic import BaseModel, Field


class PlayerRosterScopePolicy(BaseModel):
    policy_version: str
    player_scope: str
    roster_scope: str
    expected_player_count: int = Field(ge=0)
    expected_roster_count: int = Field(ge=0)


ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY = PlayerRosterScopePolicy(
    policy_version="active-nba-players-rosters.fixture.v1",
    player_scope="active NBA fixture players",
    roster_scope="2099-00 regular-season fixture rosters",
    expected_player_count=4,
    expected_roster_count=4,
)
