from enum import StrEnum

from pydantic import BaseModel


class PublicationCode(StrEnum):
    PUBLISHABLE = "publishable"
    BLOCKED_MISSING_COVERAGE = "blocked_missing_coverage"
    BLOCKED_STALE_DATA = "blocked_stale_data"
    BLOCKED_INCOMPARABLE_POPULATION = "blocked_incomparable_population"
    BLOCKED_FAILED_VALIDATION = "blocked_failed_validation"
    BLOCKED_MISSING_PROVIDER = "blocked_missing_provider"
    BLOCKED_MISSING_DATASET = "blocked_missing_dataset"
    SYNTHETIC_FIXTURE = "synthetic_fixture"
    UNSUPPORTED_SCOPE = "unsupported_scope"


class PublicationDecision(BaseModel):
    code: PublicationCode
    reason: str
    publishable: bool = False
    remediation: str | None = None
    required_coverage: dict[str, int | float | None] | None = None
    observed_coverage: dict[str, int | float | None] | None = None

    @classmethod
    def missing_dataset(cls) -> "PublicationDecision":
        return cls(
            code=PublicationCode.BLOCKED_MISSING_DATASET,
            reason="No validated dataset is available.",
            remediation="Configure a licensed provider and publish a validated dataset release.",
        )

    @classmethod
    def missing_provider(cls) -> "PublicationDecision":
        return cls(
            code=PublicationCode.BLOCKED_MISSING_PROVIDER,
            reason="No provider is configured.",
            remediation="Configure a licensed provider before publishing analytical data.",
        )

    @classmethod
    def synthetic(cls) -> "PublicationDecision":
        return cls(
            code=PublicationCode.SYNTHETIC_FIXTURE,
            reason="Synthetic fixture data is test-only and cannot be published.",
        )
