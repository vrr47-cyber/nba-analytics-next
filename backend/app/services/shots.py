from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from statistics import fmean
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, CoverageEvaluation, Game, GameProviderId, Player, PlayerProviderId, Season, Shot, SourceRun, Team, TeamProviderId
from backend.app.domain.shots import NormalizedShot, ShotResult, ShotType, distance_bucket


class ShotIngestionError(ValueError):
    pass


@dataclass(frozen=True)
class ShotCounts:
    inserted: int = 0
    updated: int = 0
    unchanged: int = 0


@dataclass(frozen=True)
class PreparedShots:
    game: Game
    rows: tuple[tuple[NormalizedShot, Team, Player, Shot | None], ...]
    counts: ShotCounts


EXPECTED_FG_MIN_OBSERVATIONS = 20
EXPECTED_FG_LOOKUP: dict[tuple[str, str], float] = {
    ("0-3", "two_point"): 0.62,
    ("4-9", "two_point"): 0.52,
    ("10-15", "two_point"): 0.43,
    ("16-23", "two_point"): 0.40,
    ("24+", "two_point"): 0.34,
    ("24+", "three_point"): 0.36,
}


def _mapping(session: Session, model: Any, provider: str, external_id: str, label: str) -> Any:
    mapping = session.scalar(select(model).where(model.provider_name == provider, model.external_id == external_id))
    if mapping is None:
        raise ShotIngestionError(f"missing canonical {label} mapping: {provider}/{external_id}")
    return mapping


def _prepare(session: Session, *, provider: str, payload: tuple[NormalizedShot, ...], game_external_id: str, complete_payload: bool, correction_mode: bool) -> PreparedShots:
    if not complete_payload:
        raise ShotIngestionError("shot ingestion requires a complete game payload")
    if not payload:
        raise ShotIngestionError("complete shot payload cannot be empty")
    provider_ids = [row.provider_shot_id for row in payload]
    if len(provider_ids) != len(set(provider_ids)):
        raise ShotIngestionError("duplicate provider shot IDs in payload")
    game_mapping = _mapping(session, GameProviderId, provider, game_external_id, "game")
    game = session.get(Game, game_mapping.game_id)
    if game is None:
        raise ShotIngestionError("game mapping points to missing canonical game")
    if game.status != "final":
        raise ShotIngestionError("shot ingestion requires a canonical final game")
    rows: list[tuple[NormalizedShot, Team, Player, Shot | None]] = []
    existing_rows = list(session.scalars(select(Shot).where(Shot.game_id == game.id, Shot.provider_name == provider)))
    existing = {row.provider_shot_id: row for row in existing_rows}
    if len(existing) != len(existing_rows):
        raise ShotIngestionError("duplicate provider shot identities already exist")
    for row in payload:
        if row.game_external_id != game_external_id:
            raise ShotIngestionError(f"shot game identity does not match payload: {row.provider_shot_id}")
        team_mapping = _mapping(session, TeamProviderId, provider, row.team_external_id, "team")
        player_mapping = _mapping(session, PlayerProviderId, provider, row.player_external_id, "player")
        team = session.get(Team, team_mapping.team_id)
        player = session.get(Player, player_mapping.player_id)
        if team is None or player is None:
            raise ShotIngestionError(f"shot mapping points to a missing canonical entity: {row.provider_shot_id}")
        if team.id not in {game.home_team_id, game.away_team_id}:
            raise ShotIngestionError(f"shot team is not a participant in the canonical game: {row.provider_shot_id}")
        current = existing.get(row.provider_shot_id)
        if current is not None:
            if current.game_id != game.id or current.team_id != team.id or current.player_id != player.id:
                raise ShotIngestionError(f"shot structural identity conflict: {row.provider_shot_id}")
            values = _values(row, game.id, team.id, player.id, current.source_run_id)
            changed = any(getattr(current, key) != value for key, value in values.items() if key not in {"game_id", "team_id", "player_id", "provider_name", "provider_shot_id"})
            if changed and not correction_mode:
                raise ShotIngestionError(f"shot correction requires correction mode: {row.provider_shot_id}")
            rows.append((row, team, player, current))
        else:
            if existing and not correction_mode:
                raise ShotIngestionError("adding shots to an existing payload requires correction mode")
            rows.append((row, team, player, None))
    inserted = sum(existing_row is None for *_, existing_row in rows)
    updated = sum(existing_row is not None and _changed(existing_row, row, game.id, team.id, player.id) for row, team, player, existing_row in rows)
    unchanged = len(rows) - inserted - updated
    return PreparedShots(game, tuple(rows), ShotCounts(inserted, updated, unchanged))


def _values(row: NormalizedShot, game_id: UUID, team_id: UUID, player_id: UUID, source_run_id: UUID) -> dict[str, Any]:
    return {"game_id": game_id, "team_id": team_id, "player_id": player_id, "provider_name": row.source.provider, "provider_shot_id": row.provider_shot_id, "period": row.period, "clock": row.clock, "sequence_number": row.sequence_number, "provider_x": row.provider_x, "provider_y": row.provider_y, "normalized_x": row.normalized_x, "normalized_y": row.normalized_y, "shot_distance": row.shot_distance, "zone_version": row.zone_version, "zone_code": row.zone_code, "shot_type": row.shot_type.value, "result": row.result.value, "point_value": row.point_value, "source_run_id": source_run_id}


def _changed(existing: Shot, row: NormalizedShot, game_id: UUID, team_id: UUID, player_id: UUID) -> bool:
    candidate = _values(row, game_id, team_id, player_id, existing.source_run_id)
    return any(getattr(existing, key) != value for key, value in candidate.items() if key not in {"game_id", "team_id", "player_id", "provider_name", "provider_shot_id", "source_run_id"})


def _persist(session: Session, prepared: PreparedShots, source_run: SourceRun) -> None:
    for row, team, player, existing in prepared.rows:
        values = _values(row, prepared.game.id, team.id, player.id, source_run.id)
        if existing is None:
            session.add(Shot(**values))
        else:
            for key, value in values.items():
                if key not in {"game_id", "team_id", "player_id", "provider_name", "provider_shot_id"}:
                    setattr(existing, key, value)


def validate_shots_reference(session: Session, *, provider: str, game_external_id: str, payload: tuple[NormalizedShot, ...], complete_payload: bool, correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare(session, provider=provider, payload=payload, game_external_id=game_external_id, complete_payload=complete_payload, correction_mode=correction_mode)
    return {"mutated": False, "counts": prepared.counts.__dict__, "source_run_created": False, "publication_status": "withheld"}


def ingest_shots_reference(session: Session, *, provider: str, game_external_id: str, payload: tuple[NormalizedShot, ...], schema_version: str, normalized_payload_fingerprint: str, complete_payload: bool, synthetic: bool, correction_mode: bool = False) -> dict[str, Any]:
    prepared = _prepare(session, provider=provider, payload=payload, game_external_id=game_external_id, complete_payload=complete_payload, correction_mode=correction_mode)
    now = datetime.now(timezone.utc)
    source_run = SourceRun(id=uuid4(), provider_name=provider, status="running", started_at=now, metadata_json={"operation": "shots", "load_timestamp": now.isoformat(), "schema_version": schema_version, "record_count": len(payload), "normalized_payload_fingerprint": normalized_payload_fingerprint, "synthetic": synthetic, "correction_mode": correction_mode})
    session.add(source_run)
    session.flush()
    try:
        _persist(session, prepared, source_run)
        blocking = ["synthetic_fixture"] if synthetic else []
        session.add(CoverageEvaluation(dataset_name="shots", evaluated_at=now, included_games=1, expected_games=1, included_entities=len(payload), expected_entities=len(payload), coverage_ratio=1, completeness_status="complete", publication_status="withheld", blocking_reasons=blocking, details={"provider": provider, "game_id": str(prepared.game.id), "source_run_id": str(source_run.id), "complete_payload": complete_payload, "shot_counts": prepared.counts.__dict__}, policy_version="phase10a-shots-v1"))
        source_run.status = "succeeded"
        source_run.completed_at = now
        source_run.metadata_json = {**(source_run.metadata_json or {}), "shots_inserted": prepared.counts.inserted, "shots_updated": prepared.counts.updated, "shots_unchanged": prepared.counts.unchanged, "publication_status": "withheld"}
        session.flush()
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        session.flush()
        raise
    return {"source_run_id": str(source_run.id), "counts": prepared.counts.__dict__, "publication_status": "withheld", "synthetic": synthetic, "release_created": False, "source_run_status": "succeeded"}


def _expected_fg(rows: list[Shot]) -> float | None:
    if len(rows) < EXPECTED_FG_MIN_OBSERVATIONS:
        return None
    values = [EXPECTED_FG_LOOKUP.get((distance_bucket(float(row.shot_distance) if row.shot_distance is not None else None) or "", row.shot_type)) for row in rows]
    known = [value for value in values if value is not None]
    return round(fmean(known), 4) if len(known) == len(values) else None


def aggregate_shots(rows: list[Shot], *, coordinates_limit: int = 100) -> dict[str, Any]:
    field_goals = [row for row in rows if row.shot_type in {ShotType.TWO_POINT.value, ShotType.THREE_POINT.value}]
    makes = [row for row in field_goals if row.result == ShotResult.MADE.value]
    three_point_attempts = [row for row in field_goals if row.shot_type == ShotType.THREE_POINT.value]
    three_point_makes = [row for row in three_point_attempts if row.result == ShotResult.MADE.value]
    expected_fg = _expected_fg(field_goals)
    return {"attempts": len(rows), "makes": sum(row.result == ShotResult.MADE.value for row in rows), "field_goal_attempts": len(field_goals), "field_goal_makes": len(makes), "three_point_attempts": len(three_point_attempts), "three_point_makes": len(three_point_makes), "fg_percentage": (len(makes) / len(field_goals) if field_goals else None), "three_point_percentage": (len(three_point_makes) / len(three_point_attempts) if three_point_attempts else None), "effective_fg_percentage": ((len(makes) + 0.5 * len(three_point_makes)) / len(field_goals) if field_goals else None), "actual_points": sum(row.point_value for row in rows if row.result == ShotResult.MADE.value), "average_distance": (fmean(float(row.shot_distance) for row in rows if row.shot_distance is not None) if any(row.shot_distance is not None for row in rows) else None), "expected_fg_percentage": expected_fg, "expected_points": (sum((EXPECTED_FG_LOOKUP.get((distance_bucket(float(row.shot_distance) if row.shot_distance is not None else None) or "", row.shot_type), 0) * row.point_value) for row in field_goals) if expected_fg is not None else None), "zone_distribution": _distribution(rows, "zone_code"), "shot_type_distribution": _distribution(rows, "shot_type"), "coordinates": [{"x": float(row.normalized_x), "y": float(row.normalized_y), "result": row.result, "shot_type": row.shot_type} for row in rows if row.normalized_x is not None and row.normalized_y is not None][:coordinates_limit]}


def _distribution(rows: list[Shot], field: str) -> list[dict[str, Any]]:
    counts = Counter(getattr(row, field) for row in rows)
    total = len(rows)
    return [{"key": key, "attempts": count, "share": count / total if total else None} for key, count in sorted(counts.items())]


def _coverage_and_provenance(session: Session, rows: list[Shot]) -> tuple[Any, Any, Any]:
    from backend.app.domain.coverage import Coverage
    from backend.app.domain.publication import PublicationDecision
    from backend.app.schemas.envelope import Provenance
    if not rows:
        return Coverage.unavailable("No validated shot dataset is available."), PublicationDecision.missing_dataset(), Provenance(metric_version="shot-analytics.v1")
    runs = [session.get(SourceRun, row.source_run_id) for row in rows]
    synthetic = any(bool((run.metadata_json or {}).get("synthetic")) for run in runs if run is not None)
    run_ids = {row.source_run_id for row in rows}
    latest = max((run for run in runs if run is not None), key=lambda run: run.completed_at or run.started_at, default=None)
    coverage = Coverage(included_games=len({row.game_id for row in rows}), expected_games=len({row.game_id for row in rows}), included_entities=len(rows), expected_entities=len(rows), coverage_ratio=1, is_complete=True, is_publishable=False, reason="Synthetic fixture shot coverage is recorded for development only." if synthetic else "Shot coverage is complete for the selected canonical sample.")
    publication = PublicationDecision.synthetic() if synthetic else PublicationDecision.from_coverage("complete")
    provenance = Provenance(source=latest.provider_name if latest else None, ingested_at=latest.completed_at if latest else None, dataset_version="phase10a-shots-v1", metric_version="shot-analytics.v1", synthetic=synthetic, contributing_source_run_count=len(run_ids))
    return coverage, publication, provenance


def shot_summary(session: Session, *, season: str | None = None, competition: str | None = None, player_id: UUID | None = None, team_id: UUID | None = None) -> tuple[dict[str, Any], Any, Any, Any]:
    query = select(Shot).join(Game, Shot.game_id == Game.id).join(Season, Game.season_id == Season.id).join(Competition, Game.competition_id == Competition.id)
    if season is not None:
        query = query.where(Season.season_code == season)
    if competition is not None:
        query = query.where(Competition.code == competition)
    rows = list(session.scalars(query))
    if player_id is not None:
        rows = [row for row in rows if row.player_id == player_id]
    if team_id is not None:
        rows = [row for row in rows if row.team_id == team_id]
    return aggregate_shots(rows), *_coverage_and_provenance(session, rows)
