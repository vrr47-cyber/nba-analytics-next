from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_services
from backend.app.database.session import check_readiness
from backend.app.schemas.status import DatasetStatus, StatusResponse
from backend.app.services.application import AppServices

router = APIRouter(prefix="/api/v1", tags=["status"])


@router.get("/status", response_model=StatusResponse)
def status(services: AppServices = Depends(get_services)) -> StatusResponse:
    db = check_readiness(services.engine)
    provider = services.provider.readiness()
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
        current_dataset=DatasetStatus(publication_status="unavailable"),
        model_versions=[],
        publication_ready=False,
        publication_reason="No validated dataset is available.",
    )
