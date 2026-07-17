from pydantic import BaseModel, Field


class GameScopePolicy(BaseModel):
    policy_version: str
    scope: str
    expected_game_count: int = Field(ge=0)
    game_date_timezone: str = "UTC"


FIXTURE_GAME_SCOPE_POLICY = GameScopePolicy(
    policy_version="fixture-games.2099-00.regular.v1",
    scope="2099-00 regular-season fixture schedule",
    expected_game_count=3,
)
