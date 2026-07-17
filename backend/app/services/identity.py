from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import GameProviderId, LeagueProviderId, PlayerProviderId, TeamProviderId


class IdentityResolutionError(ValueError):
    pass


class IdentityResolver:
    def __init__(self, session: Session):
        self.session = session

    def league(self, provider: str, external_id: str) -> UUID:
        row = self.session.scalar(select(LeagueProviderId).where(LeagueProviderId.provider_name == provider, LeagueProviderId.external_id == external_id))
        if row is None:
            raise IdentityResolutionError(f"unresolved provider league reference: {provider}/{external_id}")
        return row.league_id

    def team(self, provider: str, external_id: str) -> UUID:
        row = self.session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == external_id))
        if row is None:
            raise IdentityResolutionError(f"unresolved provider team reference: {provider}/{external_id}")
        return row.team_id

    def player(self, provider: str, external_id: str) -> UUID:
        row = self.session.scalar(select(PlayerProviderId).where(PlayerProviderId.provider_name == provider, PlayerProviderId.external_id == external_id))
        if row is None:
            raise IdentityResolutionError(f"unresolved provider player reference: {provider}/{external_id}")
        return row.player_id

    def game(self, provider: str, external_id: str) -> UUID:
        row = self.session.scalar(select(GameProviderId).where(GameProviderId.provider_name == provider, GameProviderId.external_id == external_id))
        if row is None:
            raise IdentityResolutionError(f"unresolved provider game reference: {provider}/{external_id}")
        return row.game_id
