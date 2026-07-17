from datetime import date, datetime
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from backend.app.domain.coverage import Coverage

T = TypeVar("T")


class Scope(BaseModel):
    league: str | None = None
    season: str | None = None
    competition: str | None = None
    start_date: date | None = None
    end_date: date | None = None


class Provenance(BaseModel):
    source: str | None = None
    source_updated_at: datetime | None = None
    ingested_at: datetime | None = None
    dataset_version: str | None = None
    metric_version: str | None = None
    synthetic: bool = False
    contributing_source_run_count: int | None = None


class Publication(BaseModel):
    publishable: bool
    code: str
    reason: str


class Envelope(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    data: T
    scope: Scope
    coverage: Coverage
    provenance: Provenance
