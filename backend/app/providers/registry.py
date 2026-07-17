from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from backend.app.domain.box_scores import NormalizedBoxScorePayload
from backend.app.domain.canonical import NormalizedGame, NormalizedLeague, NormalizedPlayer, NormalizedRosterEntry, NormalizedTeam
from backend.app.domain.team_scope import TeamScopePolicy
from backend.app.providers.fixture import FixtureTeamsProvider


class ProviderConfigurationError(ValueError):
    pass


class TeamsProvider(Protocol):
    name: str
    synthetic: bool

    def load_teams(self, scope: TeamScopePolicy) -> tuple[NormalizedLeague, tuple[NormalizedTeam, ...], str, str, TeamScopePolicy]: ...

    def load_players(self, revision: str = "v1") -> tuple[tuple[NormalizedPlayer, ...], str, str, str]: ...

    def load_rosters(self, revision: str = "v1") -> tuple[tuple[NormalizedRosterEntry, ...], str, str, str]: ...

    def load_games(self, revision: str = "v1") -> tuple[tuple[NormalizedGame, ...], str, str, str]: ...

    def load_box_score(self, revision: str = "v1") -> tuple[NormalizedBoxScorePayload, str, str, str]: ...


class ProviderRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, Callable[[], object]] = {"fixture": FixtureTeamsProvider}

    def register(self, name: str, factory: Callable[[], object]) -> None:
        self._factories[name] = factory

    def create(self, name: str) -> object:
        try:
            return self._factories[name]()
        except KeyError as exc:
            raise ProviderConfigurationError(f"provider is not registered: {name}") from exc


registry = ProviderRegistry()


def create_provider(name: str) -> object:
    return registry.create(name)


def create_teams_provider(name: str) -> TeamsProvider:
    provider = registry.create(name)
    if not hasattr(provider, "load_teams"):
        raise ProviderConfigurationError(f"provider does not support teams: {name}")
    return provider  # type: ignore[return-value]
