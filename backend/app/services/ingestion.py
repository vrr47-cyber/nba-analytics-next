from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from backend.app.database.models import Competition, Game, GameProviderId, League, Player, PlayerGameStats, PlayerProviderId, RosterSnapshot, Season, SourceRun, StandingsSnapshot, Team, TeamGameStats, TeamProviderId
from backend.app.database.repositories.canonical import ProviderIdentityRepository
from backend.app.domain.canonical import NormalizedCompetition, NormalizedGame, NormalizedLeague, NormalizedPlayer, NormalizedRosterEntry, NormalizedStandingsRow, NormalizedTeam
from backend.app.domain.ingestion import IngestionBatch, IngestionOutcome


@dataclass(frozen=True)
class IngestionResult:
    source_run_id: UUID
    outcome: IngestionOutcome
    rows_received: int
    rows_written: int
    warnings: tuple[str, ...] = ()


class IngestionService:
    """Transactional canonical writers. Provider adapters remain outside this service."""

    def __init__(self, session: Session):
        self.session = session

    def ingest_teams(self, batch: IngestionBatch[NormalizedTeam], league: League) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._teams(batch, league, source_run_id))

    def ingest_players(self, batch: IngestionBatch[NormalizedPlayer]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._players(batch, source_run_id))

    def ingest_leagues(self, batch: IngestionBatch[NormalizedLeague]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._leagues(batch))

    def ingest_competitions(self, batch: IngestionBatch[NormalizedCompetition], league: League) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._competitions(batch, league))

    def ingest_roster_snapshots(self, batch: IngestionBatch[NormalizedRosterEntry]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._rosters(batch, source_run_id))

    def ingest_games(self, batch: IngestionBatch[NormalizedGame]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._games(batch, source_run_id))

    def ingest_team_game_stats(self, batch: IngestionBatch[Any]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._dependent_rows(batch, source_run_id, "team_game_stats"))

    def ingest_player_game_stats(self, batch: IngestionBatch[Any]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._dependent_rows(batch, source_run_id, "player_game_stats"))

    def ingest_standings_snapshots(self, batch: IngestionBatch[NormalizedStandingsRow]) -> IngestionResult:
        return self._run(batch, lambda source_run_id: self._standings(batch, source_run_id))

    def _run(self, batch: IngestionBatch[Any], writer) -> IngestionResult:
        source_run = SourceRun(id=uuid4(), provider_name=batch.provider, status="running", started_at=datetime.now(timezone.utc), metadata_json={"operation": batch.operation, "schema_fingerprint": batch.schema_fingerprint, "rows_received": len(batch.records)})
        self.session.add(source_run)
        try:
            if batch.outcome not in {IngestionOutcome.SUCCEEDED, IngestionOutcome.SUCCEEDED_WITH_WARNINGS}:
                raise ValueError(f"batch outcome {batch.outcome} cannot be ingested")
            if not batch.records and batch.outcome == IngestionOutcome.SUCCEEDED:
                raise ValueError("empty provider response requires explicit completeness handling")
            written = writer(source_run.id)
            source_run.status = "succeeded_with_warnings" if batch.warnings else "succeeded"
            source_run.completed_at = datetime.now(timezone.utc)
            source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_written": written}
            self.session.flush()
            return IngestionResult(source_run.id, IngestionOutcome.SUCCEEDED_WITH_WARNINGS if batch.warnings else IngestionOutcome.SUCCEEDED, len(batch.records), written, tuple(batch.warnings))
        except Exception as exc:
            source_run.status = "failed"
            source_run.completed_at = datetime.now(timezone.utc)
            source_run.error_message = str(exc)
            self.session.flush()
            raise

    def _leagues(self, batch: IngestionBatch[NormalizedLeague]) -> int:
        written = 0
        for record in batch.records:
            existing = self.session.query(League).filter_by(code=record.code).one_or_none()
            if existing is None:
                self.session.add(League(code=record.code, display_name=record.display_name))
                written += 1
            else:
                existing.display_name = record.display_name
        return written

    def _competitions(self, batch: IngestionBatch[NormalizedCompetition], league: League) -> int:
        written = 0
        for record in batch.records:
            existing = self.session.query(Competition).filter_by(league_id=league.id, code=record.code).one_or_none()
            if existing is None:
                self.session.add(Competition(league_id=league.id, code=record.code, display_name=record.display_name, category=record.category))
                written += 1
            else:
                existing.display_name = record.display_name
                existing.category = record.category
        return written

    def _teams(self, batch: IngestionBatch[NormalizedTeam], league: League, source_run_id: UUID) -> int:
        written = 0
        identities = ProviderIdentityRepository(self.session)
        for record in batch.records:
            existing = self.session.query(Team).filter_by(league_id=league.id, slug=record.slug).one_or_none()
            if existing is None:
                existing = Team(league_id=league.id, slug=record.slug, full_name=record.full_name, short_name=record.short_name, abbreviation=record.abbreviation, city=record.city)
                self.session.add(existing)
                self.session.flush()
                written += 1
            else:
                existing.full_name = record.full_name
                existing.short_name = record.short_name
                existing.abbreviation = record.abbreviation
                existing.city = record.city
            identities.bind_team(record.source.provider, record.source.external_id, existing.id, datetime.fromisoformat(record.source.retrieved_at))
        return written

    def _players(self, batch: IngestionBatch[NormalizedPlayer], source_run_id: UUID):
        written = 0
        identities = ProviderIdentityRepository(self.session)
        for record in batch.records:
            existing = self.session.query(Player).filter_by(slug=record.slug).one_or_none()
            if existing is None:
                existing = Player(slug=record.slug, full_name=record.full_name, first_name=record.first_name, last_name=record.last_name, position=record.position)
                self.session.add(existing)
                self.session.flush()
                written += 1
            else:
                existing.full_name = record.full_name
                existing.first_name = record.first_name
                existing.last_name = record.last_name
                existing.position = record.position
            identities.bind_player(record.source.provider, record.source.external_id, existing.id, datetime.fromisoformat(record.source.retrieved_at))
        return written

    def _rosters(self, batch: IngestionBatch[NormalizedRosterEntry], source_run_id: UUID) -> int:
        written = 0
        for record in batch.records:
            team = self.session.query(Team).join(TeamProviderId).filter(TeamProviderId.provider_name == record.source.provider, TeamProviderId.external_id == record.team_external_id).one()
            player = self.session.query(Player).join(PlayerProviderId).filter(PlayerProviderId.provider_name == record.source.provider, PlayerProviderId.external_id == record.player_external_id).one()
            season = self.session.query(Season).filter_by(season_code=record.season).one()
            existing = self.session.query(RosterSnapshot).filter_by(season_id=season.id, team_id=team.id, player_id=player.id, snapshot_at=datetime.fromisoformat(record.snapshot_at)).one_or_none()
            if existing is None:
                self.session.add(RosterSnapshot(season_id=season.id, team_id=team.id, player_id=player.id, snapshot_at=datetime.fromisoformat(record.snapshot_at), jersey_number=record.jersey_number, listed_position=record.listed_position, roster_status=record.roster_status, source_run_id=source_run_id))
                written += 1
        return written

    def _games(self, batch: IngestionBatch[NormalizedGame], source_run_id: UUID) -> int:
        from backend.app.database.models import GameProviderId, Competition, Season
        written = 0
        for record in batch.records:
            home = self.session.query(Team).join(TeamProviderId).filter(TeamProviderId.provider_name == record.source.provider, TeamProviderId.external_id == record.home_team_external_id).one()
            away = self.session.query(Team).join(TeamProviderId).filter(TeamProviderId.provider_name == record.source.provider, TeamProviderId.external_id == record.away_team_external_id).one()
            season = self.session.query(Season).filter_by(season_code=record.season).one()
            competition = self.session.query(Competition).filter_by(league_id=season.league_id, code=record.competition_code).one()
            existing = self.session.query(Game).join(GameProviderId).filter(GameProviderId.provider_name == record.source.provider, GameProviderId.external_id == record.source.external_id).one_or_none()
            if existing is None:
                existing = Game(season_id=season.id, competition_id=competition.id, scheduled_start=datetime.fromisoformat(record.scheduled_start), game_date=record.game_date, home_team_id=home.id, away_team_id=away.id, status=record.status, home_final_score=record.home_final_score, away_final_score=record.away_final_score, neutral_site=record.neutral_site, source_run_id=source_run_id)
                self.session.add(existing)
                self.session.flush()
                self.session.add(GameProviderId(provider_name=record.source.provider, external_id=record.source.external_id, game_id=existing.id, first_observed_at=datetime.fromisoformat(record.source.retrieved_at), last_observed_at=datetime.fromisoformat(record.source.retrieved_at)))
                written += 1
            elif existing.status == "final" and record.status != "final" and not batch.correction_mode:
                raise ValueError("final game cannot regress without correction mode")
            elif existing.status == "final" and record.status == "final" and (existing.home_final_score != record.home_final_score or existing.away_final_score != record.away_final_score):
                if not batch.correction_mode:
                    raise ValueError("final score correction requires correction mode")
                existing.home_final_score = record.home_final_score
                existing.away_final_score = record.away_final_score
            else:
                existing.status = record.status
                existing.home_final_score = record.home_final_score
                existing.away_final_score = record.away_final_score
        return written

    def _standings(self, batch: IngestionBatch[NormalizedStandingsRow], source_run_id: UUID) -> int:
        from backend.app.database.models import Competition, Season
        written = 0
        for record in batch.records:
            team = self.session.query(Team).join(TeamProviderId).filter(TeamProviderId.provider_name == record.source.provider, TeamProviderId.external_id == record.team_external_id).one()
            season = self.session.query(Season).filter_by(season_code=record.season).one()
            competition = self.session.query(Competition).filter_by(league_id=season.league_id, code=record.competition_code).one()
            observed_at = datetime.fromisoformat(record.observed_at)
            if self.session.query(StandingsSnapshot).filter_by(season_id=season.id, competition_id=competition.id, team_id=team.id, observed_at=observed_at).one_or_none() is None:
                self.session.add(StandingsSnapshot(season_id=season.id, competition_id=competition.id, team_id=team.id, observed_at=observed_at, wins=record.wins, losses=record.losses, conference_rank=record.conference_rank, league_rank=record.league_rank, source_run_id=source_run_id))
                written += 1
        return written

    def _dependent_rows(self, batch: IngestionBatch[Any], source_run_id: UUID, kind: str) -> int:
        written = 0
        for record in batch.records:
            game = self.session.query(Game).join(GameProviderId).filter(GameProviderId.provider_name == record.source.provider, GameProviderId.external_id == record.game_external_id).one()
            if game.status != "final":
                raise ValueError(f"{kind} requires a final game")
            team = self.session.query(Team).join(TeamProviderId).filter(TeamProviderId.provider_name == record.source.provider, TeamProviderId.external_id == record.team_external_id).one()
            fields = record.model_dump(exclude={"source", "game_external_id", "team_external_id", "opponent_external_id", "player_external_id"}, exclude_none=False)
            fields["game_id"] = game.id
            fields["team_id"] = team.id
            fields["source_run_id"] = source_run_id
            existing: Any
            model: Any
            if kind == "team_game_stats":
                opponent = self.session.query(Team).join(TeamProviderId).filter(TeamProviderId.provider_name == record.source.provider, TeamProviderId.external_id == record.opponent_external_id).one()
                if {team.id, opponent.id} != {game.home_team_id, game.away_team_id}:
                    raise ValueError("team stat participants do not match game")
                fields["opponent_team_id"] = opponent.id
                existing = self.session.query(TeamGameStats).filter_by(game_id=game.id, team_id=team.id).one_or_none()
                model = TeamGameStats
            else:
                player = self.session.query(Player).join(PlayerProviderId).filter(PlayerProviderId.provider_name == record.source.provider, PlayerProviderId.external_id == record.player_external_id).one()
                fields["player_id"] = player.id
                existing = self.session.query(PlayerGameStats).filter_by(game_id=game.id, team_id=team.id, player_id=player.id).one_or_none()
                model = PlayerGameStats
            if existing is None:
                self.session.add(model(**fields))
                written += 1
            elif batch.correction_mode:
                for key, value in fields.items():
                    if key not in {"game_id", "team_id", "player_id", "source_run_id"}:
                        setattr(existing, key, value)
        return written
