from datetime import datetime, timezone

from backend.app.domain.canonical import NormalizedTeam, SourceMetadata
from backend.app.domain.ingestion import IngestionBatch, IngestionOutcome


def team_record(external_id: str = "fixture-team") -> NormalizedTeam:
    return NormalizedTeam(source=SourceMetadata(provider="synthetic", external_id=external_id, retrieved_at=datetime.now(timezone.utc).isoformat()), league_code="fixture-league", slug="redwood", full_name="Redwood", short_name="Redwood", abbreviation="RWD")


def test_empty_success_requires_explicit_handling():
    batch = IngestionBatch(provider="synthetic", operation="teams", retrieved_at=datetime.now(timezone.utc), records=[], outcome=IngestionOutcome.SUCCEEDED)
    assert batch.is_valid_empty is True


def test_failed_batch_is_not_a_valid_empty_result():
    batch = IngestionBatch(provider="synthetic", operation="teams", retrieved_at=datetime.now(timezone.utc), records=[], outcome=IngestionOutcome.FAILED)
    assert batch.is_valid_empty is False


def test_normalized_records_use_provider_neutral_names():
    record = team_record()
    assert record.full_name == "Redwood"
    assert not hasattr(record, "teamId")
