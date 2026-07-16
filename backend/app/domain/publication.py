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
    BLOCKED_UNKNOWN_COVERAGE = "blocked_unknown_coverage"
    BLOCKED_PARTIAL_COVERAGE = "blocked_partial_coverage"
    BLOCKED_INCONSISTENT_DATA = "blocked_inconsistent_data"
    COMPLETE_VALIDATED_DATASET = "complete_validated_dataset"


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

    @classmethod
    def from_coverage(cls, completeness: str, synthetic: bool = False) -> "PublicationDecision":
        if synthetic:
            return cls.synthetic()
        mapping = {
            "unknown": (PublicationCode.BLOCKED_UNKNOWN_COVERAGE, "Expected population is unknown."),
            "partial": (PublicationCode.BLOCKED_PARTIAL_COVERAGE, "Canonical coverage is partial."),
            "inconsistent": (PublicationCode.BLOCKED_INCONSISTENT_DATA, "Canonical data is inconsistent."),
            "stale": (PublicationCode.BLOCKED_STALE_DATA, "Canonical source data is stale."),
            "failed_validation": (PublicationCode.BLOCKED_FAILED_VALIDATION, "Canonical validation failed."),
            "empty": (PublicationCode.BLOCKED_MISSING_DATASET, "No canonical data is available."),
            "complete": (PublicationCode.COMPLETE_VALIDATED_DATASET, "Canonical coverage is complete and validated.",),
        }
        code, reason = mapping.get(completeness, (PublicationCode.BLOCKED_FAILED_VALIDATION, "Unknown coverage state."))
        return cls(code=code, reason=reason, publishable=code == PublicationCode.COMPLETE_VALIDATED_DATASET)
