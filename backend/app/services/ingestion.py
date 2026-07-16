from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.app.database.models import League, Player, SourceRun, Team
from backend.app.database.repositories.canonical import ProviderIdentityRepository
from backend.app.domain.canonical import NormalizedPlayer, NormalizedTeam
from backend.app.domain.ingestion import IngestionBatch, IngestionOutcome


@dataclass(frozen=True)
class IngestionResult:
    source_run_id: UUID
    outcome: IngestionOutcome
    rows_received: int
    rows_written: int
    warnings: tuple[str, ...] = ()


class IngestionService:
    """Transactional canonical writers. Provider adapters remain outside this service."""

    def __init__(self, session: Session):
        self.session = session

    def ingest_teams(self, batch: IngestionBatch[NormalizedTeam], league: League) -> IngestionResult:
        return self._run(batch, lambda: self._teams(batch, league))

    def ingest_players(self, batch: IngestionBatch[NormalizedPlayer]) -> IngestionResult:
        return self._run(batch, lambda: self._players(batch))

    def _run(self, batch: IngestionBatch[Any], writer) -> IngestionResult:
        source_run = SourceRun(id=uuid4(), provider_name=batch.provider, status="running", started_at=datetime.now(timezone.utc), metadata_json={"operation": batch.operation, "schema_fingerprint": batch.schema_fingerprint, "rows_received": len(batch.records)})
        self.session.add(source_run)
        try:
            if batch.outcome not in {IngestionOutcome.SUCCEEDED, IngestionOutcome.SUCCEEDED_WITH_WARNINGS}:
                raise ValueError(f"batch outcome {batch.outcome} cannot be ingested")
            if not batch.records and batch.outcome == IngestionOutcome.SUCCEEDED:
                raise ValueError("empty provider response requires explicit completeness handling")
            written = writer()
            source_run.status = "succeeded_with_warnings" if batch.warnings else "succeeded"
            source_run.completed_at = datetime.now(timezone.utc)
            source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_written": written}
            self.session.flush()
            return IngestionResult(source_run.id, IngestionOutcome.SUCCEEDED_WITH_WARNINGS if batch.warnings else IngestionOutcome.SUCCEEDED, len(batch.records), written, tuple(batch.warnings))
        except Exception as exc:
            source_run.status = "failed"
            source_run.completed_at = datetime.now(timezone.utc)
            source_run.error_message = str(exc)
            self.session.flush()
            raise

    def _teams(self, batch: IngestionBatch[NormalizedTeam], league: League) -> int:
        written = 0
        identities = ProviderIdentityRepository(self.session)
        for record in batch.records:
            existing = self.session.query(Team).filter_by(league_id=league.id, slug=record.slug).one_or_none()
            if existing is None:
                existing = Team(league_id=league.id, slug=record.slug, full_name=record.full_name, short_name=record.short_name, abbreviation=record.abbreviation, city=record.city)
                self.session.add(existing)
                self.session.flush()
                written += 1
            else:
                existing.full_name = record.full_name
                existing.short_name = record.short_name
                existing.abbreviation = record.abbreviation
                existing.city = record.city
            identities.bind_team(record.source.provider, record.source.external_id, existing.id, datetime.fromisoformat(record.source.retrieved_at))
        return written

    def _players(self, batch: IngestionBatch[NormalizedPlayer]):
        written = 0
        identities = ProviderIdentityRepository(self.session)
        for record in batch.records:
            existing = self.session.query(Player).filter_by(slug=record.slug).one_or_none()
            if existing is None:
                existing = Player(slug=record.slug, full_name=record.full_name, first_name=record.first_name, last_name=record.last_name, position=record.position)
                self.session.add(existing)
                self.session.flush()
                written += 1
            else:
                existing.full_name = record.full_name
                existing.first_name = record.first_name
                existing.last_name = record.last_name
                existing.position = record.position
            identities.bind_player(record.source.provider, record.source.external_id, existing.id, datetime.fromisoformat(record.source.retrieved_at))
        return written
