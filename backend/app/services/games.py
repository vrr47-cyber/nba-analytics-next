from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, CoverageEvaluation, Game, GameProviderId, Season, SourceRun, Team, TeamProviderId
from backend.app.database.repositories.canonical import ProviderIdentityRepository
from backend.app.domain.canonical import GameStatus, NormalizedGame
from backend.app.domain.game_scope import FIXTURE_GAME_SCOPE_POLICY, GameScopePolicy


class GameIngestionError(ValueError):
    pass


class StructuralGameIdentityConflict(GameIngestionError):
    pass


class GameStatusTransitionError(GameIngestionError):
    pass


@dataclass(frozen=True)
class _PreparedGame:
    record: NormalizedGame
    season: Season
    competition: Competition
    home_team: Team
    away_team: Team
    existing: Game | None


def _tipoff(record: NormalizedGame) -> datetime:
    value = datetime.fromisoformat(record.scheduled_start)
    if value.tzinfo is None:
        raise GameIngestionError(f"game {record.source.external_id} scheduled tipoff must include a timezone")
    return value


def _derived_game_date(tipoff: datetime) -> date:
    return tipoff.astimezone(timezone.utc).date()


def _validate_scores(record: NormalizedGame) -> None:
    has_home = record.home_final_score is not None
    has_away = record.away_final_score is not None
    if has_home != has_away:
        raise GameIngestionError(f"game {record.source.external_id} has partial final scores")
    if record.status == GameStatus.FINAL and not has_home:
        raise GameIngestionError(f"final game {record.source.external_id} requires both final scores")
    if record.status != GameStatus.FINAL and (has_home or has_away):
        raise GameIngestionError(f"non-final game {record.source.external_id} must have null final scores")


def _normal_status_transition(existing: str, incoming: GameStatus) -> bool:
    allowed: dict[str, set[GameStatus]] = {
        GameStatus.SCHEDULED: {GameStatus.SCHEDULED, GameStatus.POSTPONED, GameStatus.CANCELLED, GameStatus.FINAL},
        GameStatus.POSTPONED: {GameStatus.POSTPONED, GameStatus.SCHEDULED, GameStatus.CANCELLED, GameStatus.FINAL},
        GameStatus.CANCELLED: {GameStatus.CANCELLED},
        GameStatus.FINAL: {GameStatus.FINAL},
    }
    try:
        return incoming in allowed[existing]
    except KeyError as exc:
        raise GameStatusTransitionError(f"unsupported existing game status: {existing}") from exc


def _prepare_games(session: Session, *, provider: str, games: tuple[NormalizedGame, ...], correction_mode: bool) -> tuple[_PreparedGame, ...]:
    provider_ids = [record.source.external_id for record in games]
    if len(provider_ids) != len(set(provider_ids)):
        raise GameIngestionError("duplicate provider game IDs in one payload")
    prepared: list[_PreparedGame] = []
    for record in games:
        _validate_scores(record)
        tipoff = _tipoff(record)
        if record.game_date != _derived_game_date(tipoff).isoformat():
            raise GameIngestionError(f"game {record.source.external_id} game_date must be derived from UTC scheduled tipoff")
        home_mapping = session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == record.home_team_external_id))
        if home_mapping is None:
            raise GameIngestionError(f"missing canonical home team mapping: {provider}/{record.home_team_external_id}")
        away_mapping = session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == record.away_team_external_id))
        if away_mapping is None:
            raise GameIngestionError(f"missing canonical away team mapping: {provider}/{record.away_team_external_id}")
        home_team = session.get(Team, home_mapping.team_id)
        away_team = session.get(Team, away_mapping.team_id)
        if home_team is None or away_team is None:
            raise GameIngestionError(f"provider team mapping points to a missing canonical team for {record.source.external_id}")
        if home_team.id == away_team.id:
            raise GameIngestionError(f"game {record.source.external_id} cannot have the same home and away team")
        if home_team.league_id != away_team.league_id:
            raise GameIngestionError(f"game {record.source.external_id} home and away teams belong to different leagues")
        season = session.scalar(select(Season).where(Season.league_id == home_team.league_id, Season.season_code == record.season))
        if season is None:
            raise GameIngestionError(f"missing canonical season: league={home_team.league_id} season={record.season}")
        competition = session.scalar(select(Competition).where(Competition.league_id == home_team.league_id, Competition.code == record.competition_code))
        if competition is None:
            raise GameIngestionError(f"missing canonical competition: league={home_team.league_id} competition={record.competition_code}")
        game_mapping = session.scalar(select(GameProviderId).where(GameProviderId.provider_name == provider, GameProviderId.external_id == record.source.external_id))
        existing = session.get(Game, game_mapping.game_id) if game_mapping else None
        if game_mapping is not None and existing is None:
            raise GameIngestionError(f"provider game mapping points to a missing canonical game: {provider}/{record.source.external_id}")
        if existing is not None and (existing.season_id != season.id or existing.competition_id != competition.id or existing.home_team_id != home_team.id or existing.away_team_id != away_team.id):
            raise StructuralGameIdentityConflict(f"structural identity conflict for mapped game: {provider}/{record.source.external_id}")
        if existing is not None:
            if not _normal_status_transition(existing.status, record.status) and not (existing.status == GameStatus.FINAL and correction_mode and record.status != GameStatus.FINAL):
                raise GameStatusTransitionError(f"invalid game status transition: {existing.status} -> {record.status} for {record.source.external_id}")
            if existing.status == GameStatus.FINAL and record.status == GameStatus.FINAL and (existing.home_final_score != record.home_final_score or existing.away_final_score != record.away_final_score) and not correction_mode:
                raise GameStatusTransitionError(f"final score correction requires correction mode: {record.source.external_id}")
        prepared.append(_PreparedGame(record, season, competition, home_team, away_team, existing))
    return tuple(prepared)


def validate_games_reference(session: Session, *, provider: str, games: tuple[NormalizedGame, ...], correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare_games(session, provider=provider, games=games, correction_mode=correction_mode)
    return {"rows_received": len(prepared), "would_insert": sum(item.existing is None for item in prepared), "would_update": sum(item.existing is not None for item in prepared), "resolvable": len(prepared), "mutated": False}


def ingest_games_reference(
    session: Session,
    *,
    provider: str,
    games: tuple[NormalizedGame, ...],
    schema_version: str,
    normalized_payload_fingerprint: str,
    scope_policy: GameScopePolicy = FIXTURE_GAME_SCOPE_POLICY,
    synthetic: bool,
    correction_mode: bool = False,
) -> dict[str, Any]:
    # Prepare the entire batch before adding a SourceRun or any domain rows.
    prepared = _prepare_games(session, provider=provider, games=games, correction_mode=correction_mode)
    loaded_at = datetime.now(timezone.utc)
    source_run = SourceRun(id=uuid4(), provider_name=provider, status="running", started_at=loaded_at, metadata_json={"operation": "games", "load_timestamp": loaded_at.isoformat(), "schema_version": schema_version, "record_count": len(games), "normalized_payload_fingerprint": normalized_payload_fingerprint, "scope_policy_version": scope_policy.policy_version, "synthetic": synthetic})
    session.add(source_run)
    try:
        inserted = updated = unchanged = 0
        identities = ProviderIdentityRepository(session)
        for item in prepared:
            record = item.record
            tipoff = _tipoff(record)
            game_date = _derived_game_date(tipoff)
            source_updated_at = datetime.fromisoformat(record.source.source_updated_at) if record.source.source_updated_at else None
            if item.existing is None:
                game = Game(season_id=item.season.id, competition_id=item.competition.id, scheduled_start=tipoff, game_date=game_date, home_team_id=item.home_team.id, away_team_id=item.away_team.id, status=record.status, home_final_score=record.home_final_score, away_final_score=record.away_final_score, neutral_site=record.neutral_site, official_external_url=record.official_external_url, archival_external_url=record.archival_external_url, source_updated_at=source_updated_at, source_run_id=source_run.id)
                session.add(game)
                session.flush()
                identities.bind_game(provider, record.source.external_id, game.id, datetime.fromisoformat(record.source.retrieved_at))
                inserted += 1
                continue
            game = item.existing
            incoming_scores = (record.home_final_score, record.away_final_score)
            if game.status == GameStatus.FINAL and record.status != GameStatus.FINAL and correction_mode:
                incoming_scores = (None, None)
            mutable_values = {"scheduled_start": tipoff, "game_date": game_date, "status": record.status, "home_final_score": incoming_scores[0], "away_final_score": incoming_scores[1], "neutral_site": record.neutral_site, "official_external_url": record.official_external_url, "archival_external_url": record.archival_external_url, "source_updated_at": source_updated_at}
            changed = any(getattr(game, key) != value for key, value in mutable_values.items())
            for key, value in mutable_values.items():
                setattr(game, key, value)
            game.source_run_id = source_run.id
            identities.bind_game(provider, record.source.external_id, game.id, datetime.fromisoformat(record.source.retrieved_at))
            if changed:
                updated += 1
            else:
                unchanged += 1
        completed_at = datetime.now(timezone.utc)
        source_run.status = "succeeded"
        source_run.completed_at = completed_at
        source_run.metadata_json = {**(source_run.metadata_json or {}), "inserted": inserted, "updated": updated, "unchanged": unchanged}
        completeness = "complete" if len(games) == scope_policy.expected_game_count else "partial"
        blocking = ([] if completeness == "complete" else ["game population does not match the versioned scope policy"]) + (["synthetic_fixture"] if synthetic else [])
        session.add(CoverageEvaluation(dataset_name="games", evaluated_at=completed_at, included_games=len(games), expected_games=scope_policy.expected_game_count, included_entities=len(games), expected_entities=scope_policy.expected_game_count, coverage_ratio=(len(games) / scope_policy.expected_game_count if scope_policy.expected_game_count else None), completeness_status=completeness, publication_status="withheld", blocking_reasons=blocking, details={"scope": scope_policy.scope, "provider": provider, "source_run_id": str(source_run.id), "game_date_timezone": scope_policy.game_date_timezone}, policy_version=scope_policy.policy_version))
        return {"source_run_id": str(source_run.id), "inserted": inserted, "updated": updated, "unchanged": unchanged, "publication_status": "withheld", "synthetic": synthetic, "source_run_status": "succeeded"}
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        source_run.metadata_json = {**(source_run.metadata_json or {}), "inserted": 0, "updated": 0, "unchanged": 0}
        session.flush()
        raise
