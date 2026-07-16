from datetime import datetime, timezone

from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_services
from backend.app.database.session import check_readiness
from backend.app.schemas.health import HealthResponse, ReadinessComponent, ReadinessResponse
from backend.app.services.application import AppServices

router = APIRouter(tags=["health"])


@router.get("/health/live", response_model=HealthResponse)
def live(services: AppServices = Depends(get_services)) -> HealthResponse:
    return HealthResponse(status="ok", application_version=services.settings.app_version, timestamp=datetime.now(timezone.utc))


@router.get("/health/ready", response_model=ReadinessResponse)
def ready(services: AppServices = Depends(get_services)) -> ReadinessResponse:
    db = check_readiness(services.engine)
    provider = services.provider.readiness()
    database = ReadinessComponent(ready=db.connected and db.schema_ready, status="ready" if db.connected and db.schema_ready else "not_ready", reason=db.detail)
    provider_component = ReadinessComponent(ready=provider.ready, status="ready" if provider.ready else "not_ready", reason=provider.reason)
    dataset = ReadinessComponent(ready=False, status="not_ready", reason="No validated dataset is available.")
    ready_status = database.ready and provider_component.ready and dataset.ready
    return ReadinessResponse(status="ready" if ready_status else "not_ready", application_version=services.settings.app_version, timestamp=datetime.now(timezone.utc), database=database, provider=provider_component, dataset=dataset)
