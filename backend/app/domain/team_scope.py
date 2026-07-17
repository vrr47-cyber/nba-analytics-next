from pydantic import BaseModel, Field


class TeamScopePolicy(BaseModel):
    """Versioned expected-population policy; the mapper never owns these counts."""

    policy_version: str
    scope: str
    expected_count: int = Field(ge=0)
    eligible_league_external_ids: tuple[str, ...]


ACTIVE_TEAMS_FIXTURE_POLICY = TeamScopePolicy(
    policy_version="active-nba-teams.fixture.v1",
    scope="active NBA teams",
    expected_count=4,
    eligible_league_external_ids=("fixture-league",),
)
