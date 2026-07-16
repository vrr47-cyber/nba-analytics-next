from fastapi import APIRouter, Depends

from backend.app.api.dependencies import get_services
from backend.app.domain.coverage import Coverage
from backend.app.schemas.envelope import Envelope, Provenance, Scope
from backend.app.schemas.meta import SeasonSummary
from backend.app.services.application import AppServices

router = APIRouter(prefix="/api/v1/meta", tags=["metadata"])


@router.get("/seasons", response_model=Envelope[list[SeasonSummary]])
def seasons(services: AppServices = Depends(get_services)) -> Envelope[list[SeasonSummary]]:
    return Envelope(
        data=[], scope=Scope(), coverage=Coverage.unavailable("No validated season dataset is available."), provenance=Provenance(source=services.provider.readiness().name)
    )
