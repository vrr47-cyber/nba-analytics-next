from datetime import date

from backend.app.core.errors import ApplicationError
from backend.app.domain.provider_status import ProviderMode, ProviderReadiness
from backend.app.providers.protocols import ProviderReference, ProviderResult


class UnconfiguredProvider:
    def readiness(self) -> ProviderReadiness:
        return ProviderReadiness(
            name="unconfigured",
            mode=ProviderMode.UNCONFIGURED,
            ready=False,
            reason="No licensed data provider is configured.",
        )

    def _raise(self) -> None:
        raise ApplicationError(
            "provider_unconfigured",
            "No licensed data provider is configured; no network call was attempted.",
        )

    async def list_teams(self) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def list_players(self) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def get_roster(self, team_id: str, season: str) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def get_standings(self, season: str, competition: str) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def list_completed_games(self, start_date: date, end_date: date) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def get_team_box_score(self, game_id: str, team_id: str) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def get_player_box_score(self, game_id: str, player_id: str) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def list_shots(self, game_id: str | None = None) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def list_today_games(self) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def get_live_game_state(self, game_id: str) -> ProviderResult:
        self._raise()
        return ProviderResult()

    async def get_team_record_reference(self, team_id: str, season: str) -> ProviderReference:
        self._raise()
        return ProviderReference()

    async def get_player_season_reference(self, player_id: str, season: str) -> ProviderReference:
        self._raise()
        return ProviderReference()

    async def get_completed_game_reference(self, game_id: str) -> ProviderReference:
        self._raise()
        return ProviderReference()
