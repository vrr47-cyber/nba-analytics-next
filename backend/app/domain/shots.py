from __future__ import annotations

from enum import StrEnum
from math import hypot

from pydantic import BaseModel, Field, model_validator

from backend.app.domain.canonical import SourceMetadata


class ShotType(StrEnum):
    TWO_POINT = "two_point"
    THREE_POINT = "three_point"
    FREE_THROW = "free_throw"


class ShotResult(StrEnum):
    MADE = "made"
    MISSED = "missed"


class NormalizedShot(BaseModel):
    source: SourceMetadata
    game_external_id: str = Field(min_length=1)
    team_external_id: str = Field(min_length=1)
    player_external_id: str = Field(min_length=1)
    provider_shot_id: str = Field(min_length=1)
    period: int = Field(ge=1)
    clock: str = Field(min_length=1)
    sequence_number: int | None = Field(default=None, ge=0)
    provider_x: float | None = None
    provider_y: float | None = None
    normalized_x: float | None = None
    normalized_y: float | None = None
    shot_distance: float | None = Field(default=None, ge=0)
    zone_version: str = Field(min_length=1)
    zone_code: str = Field(min_length=1)
    shot_type: ShotType
    result: ShotResult
    point_value: int = Field(ge=0, le=3)

    @model_validator(mode="after")
    def validate_shot(self) -> "NormalizedShot":
        coordinate_pairs = ((self.provider_x, self.provider_y), (self.normalized_x, self.normalized_y))
        if any((x is None) != (y is None) for x, y in coordinate_pairs):
            raise ValueError("shot coordinates must be supplied as complete pairs")
        expected_points = {
            ShotType.TWO_POINT: 2,
            ShotType.THREE_POINT: 3,
            ShotType.FREE_THROW: 1,
        }[self.shot_type]
        if self.point_value != expected_points:
            raise ValueError("shot point value does not match shot type")
        if self.result == ShotResult.MADE and self.point_value <= 0:
            raise ValueError("made shots must have positive point value")
        return self


def normalize_coordinates(provider_x: float | None, provider_y: float | None) -> tuple[float | None, float | None]:
    if provider_x is None or provider_y is None:
        return None, None
    return round(float(provider_x), 4), round(float(provider_y), 4)


def distance_bucket(distance: float | None) -> str | None:
    if distance is None:
        return None
    if distance < 4:
        return "0-3"
    if distance < 10:
        return "4-9"
    if distance < 16:
        return "10-15"
    if distance < 24:
        return "16-23"
    return "24+"


def derived_distance(normalized_x: float | None, normalized_y: float | None, source_distance: float | None) -> float | None:
    if source_distance is not None:
        return round(float(source_distance), 3)
    if normalized_x is None or normalized_y is None:
        return None
    return round(hypot(normalized_x, normalized_y), 3)
