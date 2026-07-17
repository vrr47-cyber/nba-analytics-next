from datetime import datetime

from pydantic import BaseModel

from backend.app.domain.provider_status import ProviderMode


class DatasetStatus(BaseModel):
    release_id: str | None = None
    version: str | None = None
    publication_status: str | None = None


class StatusResponse(BaseModel):
    application_name: str
    application_version: str
    environment: str
    database_ready: bool
    database_status: str
    database_schema_version: str | None = None
    provider_name: str
    provider_ready: bool
    provider_mode: ProviderMode
    provider_reason: str
    current_dataset: DatasetStatus
    model_versions: list[str]
    latest_successful_source_run: datetime | None = None
    publication_ready: bool
    publication_reason: str
    canonical_schema_ready: bool = False
    dataset_release_count: int = 0
    latest_coverage_evaluation: str | None = None
