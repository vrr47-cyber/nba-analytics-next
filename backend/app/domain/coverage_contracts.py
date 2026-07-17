from enum import StrEnum

from pydantic import BaseModel, Field


class CompletenessState(StrEnum):
    UNKNOWN = "unknown"
    EMPTY = "empty"
    PARTIAL = "partial"
    COMPLETE = "complete"
    INCONSISTENT = "inconsistent"
    STALE = "stale"
    FAILED_VALIDATION = "failed_validation"


class CoverageEvaluationInput(BaseModel):
    dataset_name: str
    observed_count: int = Field(ge=0)
    expected_count: int | None = Field(default=None, ge=0)
    missing_identifiers: list[str] = Field(default_factory=list)
    duplicated_identifiers: list[str] = Field(default_factory=list)
    inconsistent_records: list[str] = Field(default_factory=list)
    source_fresh: bool | None = None
    policy_version: str = "phase2a-v1"


class CoverageDecision(BaseModel):
    completeness: CompletenessState
    ratio: float | None
    publishable: bool = False
    recommendation: str
    blocking_reasons: list[str] = Field(default_factory=list)
    policy_version: str


def evaluate_coverage(value: CoverageEvaluationInput) -> CoverageDecision:
    reasons: list[str] = []
    if value.inconsistent_records or value.duplicated_identifiers:
        reasons.append("Canonical records are inconsistent or duplicated.")
        state = CompletenessState.INCONSISTENT
    elif value.observed_count == 0:
        state = CompletenessState.EMPTY
        reasons.append("No canonical records are available.")
    elif value.expected_count is None:
        state = CompletenessState.UNKNOWN
        reasons.append("Expected population is unknown.")
    elif value.observed_count < value.expected_count:
        state = CompletenessState.PARTIAL
        reasons.append("Observed population is below the expected population.")
    else:
        state = CompletenessState.COMPLETE
    if value.missing_identifiers:
        reasons.append("Required identifiers are missing.")
    if value.source_fresh is False:
        state = CompletenessState.STALE
        reasons.append("Source data is stale.")
    return CoverageDecision(completeness=state, ratio=(value.observed_count / value.expected_count if value.expected_count else None), recommendation="withhold" if reasons else "review", blocking_reasons=reasons, policy_version=value.policy_version)
