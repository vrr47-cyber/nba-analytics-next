from enum import StrEnum

from pydantic import BaseModel


class ProviderMode(StrEnum):
    UNCONFIGURED = "unconfigured"
    SYNTHETIC_TEST = "synthetic-test"


class ProviderReadiness(BaseModel):
    name: str
    mode: ProviderMode
    ready: bool = False
    reason: str
