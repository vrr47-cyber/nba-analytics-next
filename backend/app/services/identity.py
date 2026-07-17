from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import GameProviderId, League, PlayerProviderId, TeamProviderId


class IdentityResolutionError(ValueError):
    pass


class IdentityResolver:
    def __init__(self, session: Session):
        self.session = session

    def league(self, provider: str, external_id: str) -> UUID:
        # League mappings are represented by the stable provider metadata code until
        # a dedicated league_provider_ids table is required by a licensed source.
        row = self.session.scalar(select(League).where(League.code == external_id))
        if row is None:
            raise IdentityResolutionError(f"unresolved provider league reference: {provider}/{external_id}")
        return row.id

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
