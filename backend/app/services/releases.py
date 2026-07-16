from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session

from backend.app.database.models import DatasetRelease
from backend.app.domain.publication import PublicationDecision


class ReleaseError(ValueError):
    pass


def create_release(session: Session, *, dataset_name: str, version: str, synthetic: bool, validation_status: str, coverage: dict, manifest_checksum: str | None, manifest_reference: str | None, generating_commit: str | None = None) -> DatasetRelease:
    if session.query(DatasetRelease).filter_by(dataset_name=dataset_name, version=version).one_or_none() is not None:
        raise ReleaseError("dataset release version already exists and releases are immutable")
    decision = PublicationDecision.synthetic() if synthetic else PublicationDecision.from_coverage(coverage.get("completeness", "unknown"))
    release = DatasetRelease(dataset_name=dataset_name, version=version, status="validated" if validation_status == "passed" else "rejected", schema_version="phase2b-v1", validation_status=validation_status, publication_status="withheld" if not decision.publishable else "publishable", coverage_json=coverage, provenance_json={"synthetic": synthetic}, manifest_checksum=manifest_checksum, manifest_reference=manifest_reference, generating_commit=generating_commit, released_at=datetime.now(timezone.utc) if validation_status == "passed" else None)
    session.add(release)
    return release
