from datetime import datetime
from enum import StrEnum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field


class IngestionOutcome(StrEnum):
    SUCCEEDED = "succeeded"
    SUCCEEDED_WITH_WARNINGS = "succeeded_with_warnings"
    FAILED = "failed"
    REJECTED_SCHEMA_CHANGE = "rejected_schema_change"
    REJECTED_VALIDATION = "rejected_validation"
    REJECTED_UNSUPPORTED_SCOPE = "rejected_unsupported_scope"


class IngestionScope(BaseModel):
    league: str | None = None
    season: str | None = None
    competition: str | None = None
    start_date: str | None = None
    end_date: str | None = None


T = TypeVar("T")


class IngestionBatch(BaseModel, Generic[T]):
    provider: str = Field(min_length=1)
    operation: str = Field(min_length=1)
    retrieved_at: datetime
    source_updated_at: datetime | None = None
    schema_fingerprint: str | None = None
    request_scope: IngestionScope = IngestionScope()
    records: list[T] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    source_completeness: dict[str, Any] | None = None
    outcome: IngestionOutcome
    correction_mode: bool = False

    @property
    def is_valid_empty(self) -> bool:
        return not self.records and self.outcome in {IngestionOutcome.SUCCEEDED, IngestionOutcome.SUCCEEDED_WITH_WARNINGS}
