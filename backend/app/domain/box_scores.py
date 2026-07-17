from pydantic import BaseModel, Field

from backend.app.domain.canonical import NormalizedPlayerGameStats, NormalizedTeamGameStats


class NormalizedBoxScorePayload(BaseModel):
    game_external_id: str = Field(min_length=1)
    team_stats: tuple[NormalizedTeamGameStats, ...]
    player_stats: tuple[NormalizedPlayerGameStats, ...]
    complete_roster_coverage: bool = False
