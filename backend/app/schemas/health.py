from datetime import datetime

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    application_version: str
    timestamp: datetime


class ReadinessComponent(BaseModel):
    ready: bool
    status: str
    reason: str
    schema_version: str | None = None


class ReadinessResponse(BaseModel):
    status: str
    application_version: str
    timestamp: datetime
    database: ReadinessComponent
    provider: ReadinessComponent
    dataset: ReadinessComponent
