from __future__ import annotations

from datetime import datetime
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import (
    Competition, CoverageEvaluation, DatasetRelease, Game, GameProviderId, League, Player, PlayerGameStats,
    PlayerProviderId, RosterSnapshot, Season, StandingsSnapshot, Team,
    TeamGameStats, TeamProviderId, SourceRun,
)


class RepositoryError(Exception):
    pass


T = TypeVar("T")


class _Repository(Generic[T]):
    model: type[T]

    def __init__(self, session: Session):
        self.session = session

    def get(self, identifier: UUID) -> T | None:
        return self.session.get(self.model, identifier)

    def add(self, entity: T) -> T:
        self.session.add(entity)
        return entity


class SeasonRepository(_Repository[Season]):
    model = Season

    def by_code(self, league_id: UUID, season_code: str) -> Season | None:
        return self.session.scalar(select(Season).where(Season.league_id == league_id, Season.season_code == season_code))


class LeagueRepository(_Repository[League]):
    model = League

    def by_code(self, code: str) -> League | None:
        return self.session.scalar(select(League).where(League.code == code))


class CompetitionRepository(_Repository[Competition]):
    model = Competition

    def by_code(self, league_id: UUID, code: str) -> Competition | None:
        return self.session.scalar(select(Competition).where(Competition.league_id == league_id, Competition.code == code))


class TeamRepository(_Repository[Team]):
    model = Team

    def by_slug(self, league_id: UUID, slug: str) -> Team | None:
        return self.session.scalar(select(Team).where(Team.league_id == league_id, Team.slug == slug))


class PlayerRepository(_Repository[Player]):
    model = Player

    def by_slug(self, slug: str) -> Player | None:
        return self.session.scalar(select(Player).where(Player.slug == slug))


class RosterRepository(_Repository[RosterSnapshot]):
    model = RosterSnapshot


class GameRepository(_Repository[Game]):
    model = Game


class BoxScoreRepository:
    def __init__(self, session: Session):
        self.session = session

    def team_rows(self) -> list[TeamGameStats]:
        return list(self.session.scalars(select(TeamGameStats)))

    def player_rows(self) -> list[PlayerGameStats]:
        return list(self.session.scalars(select(PlayerGameStats)))


class TeamGameStatsRepository(_Repository[TeamGameStats]):
    model = TeamGameStats


class PlayerGameStatsRepository(_Repository[PlayerGameStats]):
    model = PlayerGameStats


class StandingsRepository(_Repository[StandingsSnapshot]):
    model = StandingsSnapshot


class CoverageRepository(_Repository[CoverageEvaluation]):
    model = CoverageEvaluation


class SourceRunRepository(_Repository[SourceRun]):
    model = SourceRun


class DatasetReleaseRepository(_Repository[DatasetRelease]):
    model = DatasetRelease


class ProviderIdentityRepository:
    def __init__(self, session: Session):
        self.session = session

    def bind_team(self, provider: str, external_id: str, team_id: UUID, observed_at: datetime) -> TeamProviderId:
        existing = self.session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == external_id))
        if existing and existing.team_id != team_id:
            raise RepositoryError("provider team ID is already mapped to another canonical team")
        if existing:
            existing.last_observed_at = observed_at
            return existing
        row = TeamProviderId(provider_name=provider, external_id=external_id, team_id=team_id, first_observed_at=observed_at, last_observed_at=observed_at)
        self.session.add(row)
        return row

    def bind_player(self, provider: str, external_id: str, player_id: UUID, observed_at: datetime) -> PlayerProviderId:
        existing = self.session.scalar(select(PlayerProviderId).where(PlayerProviderId.provider_name == provider, PlayerProviderId.external_id == external_id))
        if existing and existing.player_id != player_id:
            raise RepositoryError("provider player ID is already mapped to another canonical player")
        if existing:
            existing.last_observed_at = observed_at
            return existing
        row = PlayerProviderId(provider_name=provider, external_id=external_id, player_id=player_id, first_observed_at=observed_at, last_observed_at=observed_at)
        self.session.add(row)
        return row

    def bind_game(self, provider: str, external_id: str, game_id: UUID, observed_at: datetime) -> GameProviderId:
        existing = self.session.scalar(select(GameProviderId).where(GameProviderId.provider_name == provider, GameProviderId.external_id == external_id))
        if existing and existing.game_id != game_id:
            raise RepositoryError("provider game ID is already mapped to another canonical game")
        if existing:
            existing.last_observed_at = observed_at
            return existing
        row = GameProviderId(provider_name=provider, external_id=external_id, game_id=game_id, first_observed_at=observed_at, last_observed_at=observed_at)
        self.session.add(row)
        return row
