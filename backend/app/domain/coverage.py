from pydantic import BaseModel, Field


class Coverage(BaseModel):
    included_games: int = Field(default=0, ge=0)
    expected_games: int | None = Field(default=None, ge=0)
    included_entities: int = Field(default=0, ge=0)
    expected_entities: int | None = Field(default=None, ge=0)
    coverage_ratio: float | None = Field(default=None, ge=0, le=1)
    is_complete: bool = False
    is_publishable: bool = False
    reason: str

    @classmethod
    def unavailable(cls, reason: str = "No validated dataset is available.") -> "Coverage":
        return cls(reason=reason)
