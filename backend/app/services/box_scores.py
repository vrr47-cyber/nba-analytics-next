from __future__ import annotations

import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import (
    CoverageEvaluation,
    Game,
    GameProviderId,
    Player,
    PlayerGameStats,
    PlayerProviderId,
    RosterSnapshot,
    SourceRun,
    Team,
    TeamGameStats,
    TeamProviderId,
)
from backend.app.domain.box_scores import NormalizedBoxScorePayload
from backend.app.domain.canonical import NormalizedPlayerGameStats, ParticipationStatus


class BoxScoreIngestionError(ValueError):
    pass


@dataclass(frozen=True)
class RowCounts:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


@dataclass(frozen=True)
class _Prepared:
    game: Game
    teams: tuple[tuple[Any, Team], ...]
    players: tuple[tuple[Any, Player, Team], ...]
    team_existing: tuple[TeamGameStats | None, ...]
    player_existing: tuple[PlayerGameStats | None, ...]


_MINUTES = re.compile(r"^\d+:[0-5]\d$")
_LINE_FIELDS = (
    "points", "field_goals_made", "field_goals_attempted", "three_pointers_made",
    "three_pointers_attempted", "free_throws_made", "free_throws_attempted",
    "offensive_rebounds", "defensive_rebounds", "total_rebounds", "assists", "steals",
    "blocks", "turnovers", "personal_fouls", "plus_minus",
)
_PLAYER_FIELDS = ("starter", "participation_status", "status_comment", "minutes", *_LINE_FIELDS)
_TEAM_FIELDS = ("home_away", "result", "minutes", *_LINE_FIELDS)


def _parse_minutes(value: str | None, *, provider_player_id: str) -> int:
    if value is None or not _MINUTES.fullmatch(value):
        raise BoxScoreIngestionError(f"malformed or missing minutes for player {provider_player_id}")
    minutes, seconds = value.split(":")
    total = int(minutes) * 60 + int(seconds)
    if total <= 0:
        raise BoxScoreIngestionError(f"zero minutes are not supported for played player {provider_player_id}")
    return total


def _validate_participation(row: Any) -> None:
    if row.participation_status == ParticipationStatus.DID_NOT_PLAY:
        if row.minutes is not None or row.plus_minus is not None:
            raise BoxScoreIngestionError(f"DNP player {row.player_external_id} must have null minutes and plus/minus")
        if any(getattr(row, field) != 0 for field in _LINE_FIELDS if field != "plus_minus"):
            raise BoxScoreIngestionError(f"DNP player {row.player_external_id} must have zero counting stats")
        return
    _parse_minutes(row.minutes, provider_player_id=row.player_external_id)


def _line_values(row: Any, fields: tuple[str, ...]) -> dict[str, Any]:
    return {field: getattr(row, field) for field in fields}


def _team_values(row: Any, opponent_id: UUID) -> dict[str, Any]:
    return _line_values(row, _TEAM_FIELDS) | {"opponent_team_id": opponent_id}


def _opponent_id(teams: dict[str, Team], row: Any) -> UUID:
    return teams[row.opponent_external_id].id


def _prepared_opponent_id(prepared: _Prepared, row: Any) -> UUID:
    return next(team.id for candidate, team in prepared.teams if candidate.team_external_id == row.opponent_external_id)


def _changed(existing: Any, values: dict[str, Any]) -> bool:
    return any(getattr(existing, field) != value for field, value in values.items())


def _resolve_team(session: Session, provider: str, external_id: str, label: str) -> Team:
    mapping = session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == external_id))
    if mapping is None:
        raise BoxScoreIngestionError(f"missing canonical {label} team mapping: {provider}/{external_id}")
    team = session.get(Team, mapping.team_id)
    if team is None:
        raise BoxScoreIngestionError(f"canonical team mapping points to missing team: {provider}/{external_id}")
    return team


def _prepare(session: Session, *, provider: str, payload: NormalizedBoxScorePayload, correction_mode: bool) -> _Prepared:
    game_mapping = session.scalar(select(GameProviderId).where(GameProviderId.provider_name == provider, GameProviderId.external_id == payload.game_external_id))
    if game_mapping is None:
        raise BoxScoreIngestionError(f"missing canonical game mapping: {provider}/{payload.game_external_id}")
    game = session.get(Game, game_mapping.game_id)
    if game is None:
        raise BoxScoreIngestionError("canonical game mapping points to missing game")
    if game.status != "final":
        raise BoxScoreIngestionError("box scores require a canonical final game")
    if len(payload.team_stats) != 2:
        raise BoxScoreIngestionError("complete box score requires exactly two team-stat rows")
    team_ids = [row.team_external_id for row in payload.team_stats]
    if len(set(team_ids)) != 2:
        raise BoxScoreIngestionError("duplicate or missing team-stat participant")
    resolved_teams: dict[str, Team] = {}
    for row in payload.team_stats:
        team = _resolve_team(session, provider, row.team_external_id, "box-score")
        opponent = _resolve_team(session, provider, row.opponent_external_id, "opponent")
        if team.id == opponent.id or {team.id, opponent.id} != {game.home_team_id, game.away_team_id}:
            raise BoxScoreIngestionError("box-score teams do not match canonical game participants")
        if row.home_away not in {"home", "away"}:
            raise BoxScoreIngestionError("box-score home_away must be home or away")
        if row.home_away == "home" and team.id != game.home_team_id:
            raise BoxScoreIngestionError("home box-score row does not match canonical home team")
        if row.home_away == "away" and team.id != game.away_team_id:
            raise BoxScoreIngestionError("away box-score row does not match canonical away team")
        resolved_teams[row.team_external_id] = team
        if row.points != (game.home_final_score if team.id == game.home_team_id else game.away_final_score):
            raise BoxScoreIngestionError("team points do not match canonical final game score")
    player_ids = [row.player_external_id for row in payload.player_stats]
    if len(player_ids) != len(set(player_ids)):
        raise BoxScoreIngestionError("duplicate provider player IDs in complete box score")
    players: list[tuple[NormalizedPlayerGameStats, Player, Team]] = []
    seen_canonical: set[UUID] = set()
    points_by_team: Counter[UUID] = Counter()
    for player_row in payload.player_stats:
        _validate_participation(player_row)
        player_team = resolved_teams.get(player_row.team_external_id)
        if player_team is None:
            raise BoxScoreIngestionError("player row references an unrelated team")
        mapping = session.scalar(select(PlayerProviderId).where(PlayerProviderId.provider_name == provider, PlayerProviderId.external_id == player_row.player_external_id))
        if mapping is None:
            raise BoxScoreIngestionError(f"missing canonical player mapping: {provider}/{player_row.player_external_id}")
        player = session.get(Player, mapping.player_id)
        if player is None:
            raise BoxScoreIngestionError("canonical player mapping points to missing player")
        if player.id in seen_canonical:
            raise BoxScoreIngestionError("duplicate canonical player in complete box score")
        seen_canonical.add(player.id)
        points_by_team[player_team.id] += player_row.points
        players.append((player_row, player, player_team))
    for external_id, team in resolved_teams.items():
        team_row = next(row for row in payload.team_stats if row.team_external_id == external_id)
        if points_by_team[team.id] != team_row.points:
            raise BoxScoreIngestionError("player points do not equal team box-score points")
    if payload.complete_roster_coverage:
        _validate_roster_observation(session, game, tuple(players))
    team_existing = tuple(session.scalar(select(TeamGameStats).where(TeamGameStats.game_id == game.id, TeamGameStats.team_id == resolved_teams[row.team_external_id].id)) for row in payload.team_stats)
    if not correction_mode:
        for team_existing_row, team_row in zip(team_existing, payload.team_stats, strict=True):
            if team_existing_row is not None and _changed(team_existing_row, _team_values(team_row, _opponent_id(resolved_teams, team_row))):
                raise BoxScoreIngestionError("team-statistical correction requires correction mode")
    player_existing: list[PlayerGameStats | None] = []
    for _row, player, team in players:
        rows = list(session.scalars(select(PlayerGameStats).where(PlayerGameStats.game_id == game.id, PlayerGameStats.player_id == player.id)))
        if len(rows) > 1:
            raise BoxScoreIngestionError("duplicate canonical player stat rows already exist")
        player_existing_row = rows[0] if rows else None
        if player_existing_row is not None and player_existing_row.team_id != team.id:
            raise BoxScoreIngestionError("player team attribution is immutable")
        player_existing.append(player_existing_row)
    if not correction_mode:
        for player_existing_row, (player_row, _, _) in zip(player_existing, players, strict=True):
            if player_existing_row is not None and _changed(player_existing_row, _line_values(player_row, _PLAYER_FIELDS)):
                raise BoxScoreIngestionError("statistical or participation correction requires correction mode")
    return _Prepared(game, tuple((row, resolved_teams[row.team_external_id]) for row in payload.team_stats), tuple(players), team_existing, tuple(player_existing))


def _validate_roster_observation(session: Session, game: Game, players: tuple[tuple[Any, Player, Team], ...]) -> None:
    by_team: dict[UUID, list[Player]] = defaultdict(list)
    for _, player, team in players:
        by_team[team.id].append(player)
    for team_id, rows in by_team.items():
        snapshots = list(session.scalars(select(RosterSnapshot).where(RosterSnapshot.season_id == game.season_id, RosterSnapshot.competition_id == game.competition_id, RosterSnapshot.team_id == team_id, RosterSnapshot.snapshot_at <= datetime.combine(game.game_date, datetime.max.time(), tzinfo=timezone.utc))))
        if not snapshots:
            raise BoxScoreIngestionError("complete box score requires a roster observation on or before game date")
        latest = max(row.snapshot_at for row in snapshots)
        observed = {row.player_id for row in snapshots if row.snapshot_at == latest}
        if {player.id for player in rows} != observed:
            raise BoxScoreIngestionError("complete box score players do not match latest roster observation")


def validate_box_score_reference(session: Session, *, provider: str, payload: NormalizedBoxScorePayload, correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare(session, provider=provider, payload=payload, correction_mode=correction_mode)
    team_counts, player_counts = _counts(prepared, payload)
    return {"mutated": False, "team_counts": team_counts.__dict__, "player_counts": player_counts.__dict__, "source_run_created": False, "publication_status": "withheld"}


def _counts(prepared: _Prepared, payload: NormalizedBoxScorePayload) -> tuple[RowCounts, RowCounts]:
    team_inserted = team_updated = team_unchanged = 0
    for existing, (row, _) in zip(prepared.team_existing, prepared.teams, strict=True):
        values = _team_values(row, _prepared_opponent_id(prepared, row))
        if existing is None:
            team_inserted += 1
        elif _changed(existing, values):
            team_updated += 1
        else:
            team_unchanged += 1
    player_inserted = player_updated = player_unchanged = 0
    for player_existing_row, (row, _, _) in zip(prepared.player_existing, prepared.players, strict=True):
        if player_existing_row is None:
            player_inserted += 1
        elif _changed(player_existing_row, _line_values(row, _PLAYER_FIELDS)):
            player_updated += 1
        else:
            player_unchanged += 1
    return RowCounts(team_inserted, team_updated, team_unchanged), RowCounts(player_inserted, player_updated, player_unchanged)


def ingest_box_score_reference(session: Session, *, provider: str, payload: NormalizedBoxScorePayload, schema_version: str, normalized_payload_fingerprint: str, synthetic: bool, correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare(session, provider=provider, payload=payload, correction_mode=correction_mode)
    team_counts, player_counts = _counts(prepared, payload)
    now = datetime.now(timezone.utc)
    source_run = SourceRun(id=uuid4(), provider_name=provider, status="running", started_at=now, metadata_json={"operation": "box_scores", "load_timestamp": now.isoformat(), "schema_version": schema_version, "record_count": len(payload.team_stats) + len(payload.player_stats), "normalized_payload_fingerprint": normalized_payload_fingerprint, "synthetic": synthetic, "correction_mode": correction_mode})
    session.add(source_run)
    session.flush()
    try:
        for existing, (row, team) in zip(prepared.team_existing, prepared.teams, strict=True):
            values = _team_values(row, _prepared_opponent_id(prepared, row)) | {"game_id": prepared.game.id, "team_id": team.id, "source_run_id": source_run.id, "source_updated_at": datetime.fromisoformat(row.source.source_updated_at) if row.source.source_updated_at else now}
            if existing is None:
                session.add(TeamGameStats(**values))
            else:
                for field, value in values.items():
                    if field not in {"game_id", "team_id"}:
                        setattr(existing, field, value)
        for player_existing_row, (row, player, team) in zip(prepared.player_existing, prepared.players, strict=True):
            values = _line_values(row, _PLAYER_FIELDS) | {"game_id": prepared.game.id, "player_id": player.id, "team_id": team.id, "source_run_id": source_run.id, "source_updated_at": datetime.fromisoformat(row.source.source_updated_at) if row.source.source_updated_at else now}
            if player_existing_row is None:
                session.add(PlayerGameStats(**values))
            else:
                for field, value in values.items():
                    if field not in {"game_id", "player_id", "team_id"}:
                        setattr(player_existing_row, field, value)
        blocking = ["synthetic_fixture"] if synthetic else []
        status = "complete" if not blocking else "complete"
        for dataset, count, expected in (("team_game_stats", len(payload.team_stats), 2), ("player_game_stats", len(payload.player_stats), len(payload.player_stats))):
            session.add(CoverageEvaluation(dataset_name=dataset, evaluated_at=now, included_games=1, expected_games=1, included_entities=count, expected_entities=expected, coverage_ratio=1, completeness_status=status, publication_status="withheld", blocking_reasons=blocking, details={"provider": provider, "game_id": str(prepared.game.id), "source_run_id": str(source_run.id), "complete_payload": True, "roster_validation": "latest_snapshot_on_or_before_game_date"}, policy_version="phase5-box-scores-v1"))
        source_run.status = "succeeded"
        source_run.completed_at = now
        source_run.metadata_json = {**(source_run.metadata_json or {}), "team_rows_inserted": team_counts.inserted, "team_rows_updated": team_counts.updated, "team_rows_unchanged": team_counts.unchanged, "player_rows_inserted": player_counts.inserted, "player_rows_updated": player_counts.updated, "player_rows_unchanged": player_counts.unchanged, "publication_status": "withheld"}
        session.flush()
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        session.flush()
        raise
    return {"source_run_id": str(source_run.id), "team_counts": team_counts.__dict__, "player_counts": player_counts.__dict__, "publication_status": "withheld", "synthetic": synthetic, "release_created": False}
