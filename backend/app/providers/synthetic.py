from datetime import date

from backend.app.domain.provider_status import ProviderMode, ProviderReadiness
from backend.app.providers.protocols import ProviderReference, ProviderResult


class SyntheticFixtureProvider:
    """Invented test fixtures. Never use this provider for product publication."""

    def readiness(self) -> ProviderReadiness:
        return ProviderReadiness(
            name="synthetic-fixture",
            mode=ProviderMode.SYNTHETIC_TEST,
            ready=True,
            reason="Synthetic fixtures are available for tests only.",
        )

    @staticmethod
    def _result(*records: dict[str, object]) -> ProviderResult:
        return ProviderResult(records=tuple(records), synthetic=True, publication_ready=False)

    async def list_teams(self) -> ProviderResult:
        return self._result({"team_id": "synthetic-team-redwood", "name": "Redwood"})

    async def list_players(self) -> ProviderResult:
        return self._result({"player_id": "synthetic-player-ember", "name": "Ember Vale"})

    async def get_roster(self, team_id: str, season: str) -> ProviderResult:
        return self._result({"team_id": team_id, "season": season, "player_id": "synthetic-player-ember"})

    async def get_standings(self, season: str, competition: str) -> ProviderResult:
        return self._result({"season": season, "competition": competition, "team_id": "synthetic-team-redwood"})

    async def list_completed_games(self, start_date: date, end_date: date) -> ProviderResult:
        return self._result({"game_id": "synthetic-game-001", "start_date": start_date.isoformat(), "end_date": end_date.isoformat()})

    async def get_team_box_score(self, game_id: str, team_id: str) -> ProviderResult:
        return self._result({"game_id": game_id, "team_id": team_id})

    async def get_player_box_score(self, game_id: str, player_id: str) -> ProviderResult:
        return self._result({"game_id": game_id, "player_id": player_id})

    async def list_shots(self, game_id: str | None = None) -> ProviderResult:
        return self._result({"game_id": game_id or "synthetic-game-001", "shot_id": "synthetic-shot-001"})

    async def list_today_games(self) -> ProviderResult:
        return self._result({"game_id": "synthetic-game-001", "status": "synthetic"})

    async def get_live_game_state(self, game_id: str) -> ProviderResult:
        return self._result({"game_id": game_id, "state": "synthetic"})

    async def get_team_record_reference(self, team_id: str, season: str) -> ProviderReference:
        return ProviderReference({"team_id": team_id, "season": season}, synthetic=True)

    async def get_player_season_reference(self, player_id: str, season: str) -> ProviderReference:
        return ProviderReference({"player_id": player_id, "season": season}, synthetic=True)

    async def get_completed_game_reference(self, game_id: str) -> ProviderReference:
        return ProviderReference({"game_id": game_id}, synthetic=True)
