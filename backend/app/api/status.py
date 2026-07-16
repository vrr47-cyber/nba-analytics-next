from fastapi import APIRouter, Depends
from sqlalchemy import text

from backend.app.api.dependencies import get_services
from backend.app.database.session import check_readiness
from backend.app.schemas.status import DatasetStatus, StatusResponse
from backend.app.services.application import AppServices

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/status", response_model=StatusResponse)
def status(services: AppServices = Depends(get_services)) -> StatusResponse:
    db = check_readiness(services.engine)
    provider = services.provider.readiness()
    releases = 0
    latest_coverage = None
    latest_release = None
    latest_source_run = None
    if db.connected and db.schema_ready and services.engine is not None:
        with services.engine.connect() as connection:
            releases = int(connection.execute(text("SELECT count(*) FROM dataset_releases")).scalar_one())
            latest_coverage = connection.execute(text("SELECT completeness_status FROM coverage_evaluations ORDER BY evaluated_at DESC LIMIT 1")).scalar_one_or_none()
            latest_release = connection.execute(text("SELECT publication_status FROM dataset_releases ORDER BY released_at DESC NULLS LAST LIMIT 1")).scalar_one_or_none()
            latest_source_run = connection.execute(text("SELECT completed_at FROM source_runs WHERE status IN ('succeeded','succeeded_with_warnings') ORDER BY completed_at DESC LIMIT 1")).scalar_one_or_none()
    return StatusResponse(
        application_name=services.settings.app_name,
        application_version=services.settings.app_version,
        environment=services.settings.environment,
        database_ready=db.connected and db.schema_ready,
        database_status=db.detail,
        provider_name=provider.name,
        provider_ready=provider.ready,
        provider_mode=provider.mode,
        provider_reason=provider.reason,
        model_versions=[],
        publication_ready=False,
        publication_reason="No validated dataset is available.",
        canonical_schema_ready=db.schema_ready,
        dataset_release_count=releases,
        latest_coverage_evaluation=latest_coverage,
        current_dataset=DatasetStatus(publication_status=latest_release),
        latest_successful_source_run=latest_source_run,
    )
