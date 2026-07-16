from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from backend.app.core.config import Settings
from backend.app.database.session import build_engine
from sqlalchemy.engine import Engine
from backend.app.domain.provider_status import ProviderReadiness
from backend.app.providers.synthetic import SyntheticFixtureProvider
from backend.app.providers.unconfigured import UnconfiguredProvider


class ProviderService(Protocol):
    def readiness(self) -> ProviderReadiness: ...


@dataclass
class AppServices:
    settings: Settings
    provider: ProviderService
    engine: Engine | None


def build_services(settings: Settings) -> AppServices:
    provider = SyntheticFixtureProvider() if settings.provider_mode == "synthetic-test" else UnconfiguredProvider()
    return AppServices(settings=settings, provider=provider, engine=build_engine(settings.database_url))
