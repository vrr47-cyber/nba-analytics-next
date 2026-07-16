from pydantic import BaseModel


class SeasonSummary(BaseModel):
    season: str
    competitions: list[str]
