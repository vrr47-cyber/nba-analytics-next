from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from backend.app.database.models import CoverageEvaluation, DatasetRelease, League, Season
from backend.app.domain.canonical import (
    NormalizedCompetition, NormalizedGame, NormalizedLeague, NormalizedPlayer,
    NormalizedPlayerGameStats, NormalizedRosterEntry, NormalizedSeason,
    NormalizedStandingsRow, NormalizedTeam, NormalizedTeamGameStats,
)
from backend.app.domain.ingestion import IngestionBatch, IngestionOutcome
from backend.app.services.ingestion import IngestionService
from backend.app.services.releases import create_release


class BundleFile(BaseModel):
    path: str
    rows: int = Field(ge=0)
    sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    schema_fingerprint: str = Field(min_length=1)
    required: bool = True


class BundleManifest(BaseModel):
    format_version: str = "1"
    dataset_name: str
    dataset_version: str
    provider: str
    generated_at: str
    source_updated_at: str | None = None
    league_scope: list[str] = Field(default_factory=list)
    season_scope: list[str] = Field(default_factory=list)
    competition_scope: list[str] = Field(default_factory=list)
    files: list[BundleFile]
    expected_entities: int | None = None
    expected_games: int | None = None
    synthetic: bool = False
    license_reference: str | None = None
    warnings: list[str] = Field(default_factory=list)
    generating_tool_version: str

    @field_validator("format_version")
    @classmethod
    def supported_version(cls, value: str) -> str:
        if value != "1":
            raise ValueError(f"unsupported bundle format version: {value}")
        return value


class BundleValidation(BaseModel):
    manifest: BundleManifest
    records: dict[str, list[dict[str, Any]]]
    warnings: list[str] = Field(default_factory=list)


class BundleError(ValueError):
    pass


def _safe_path(root: Path, relative: str) -> Path:
    path = Path(relative)
    if path.is_absolute() or ".." in path.parts:
        raise BundleError(f"path traversal rejected: {relative}")
    resolved = (root / path).resolve()
    if root.resolve() not in resolved.parents:
        raise BundleError(f"path escapes bundle root: {relative}")
    return resolved


def validate_bundle(bundle_root: str | Path) -> BundleValidation:
    root = Path(bundle_root).resolve()
    manifest_path = _safe_path(root, "manifest.json")
    try:
        manifest = BundleManifest.model_validate_json(manifest_path.read_text())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        raise BundleError(f"invalid manifest: {exc}") from exc
    records: dict[str, list[dict[str, Any]]] = {}
    declared = {item.path for item in manifest.files}
    for item in manifest.files:
        path = _safe_path(root, item.path)
        if not path.exists():
            if item.required:
                raise BundleError(f"missing required bundle file: {item.path}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != item.sha256:
            raise BundleError(f"checksum mismatch: {item.path}")
        rows: list[dict[str, Any]] = []
        for line_number, line in enumerate(path.read_text().splitlines(), 1):
            try:
                value = json.loads(line)
                if not isinstance(value, dict):
                    raise ValueError("record must be an object")
                rows.append(value)
            except (json.JSONDecodeError, ValueError) as exc:
                raise BundleError(f"malformed JSON Lines at {item.path}:{line_number}: {exc}") from exc
        if len(rows) != item.rows:
            raise BundleError(f"row count mismatch: {item.path}")
        records[Path(item.path).stem] = rows
    undeclared = [path.name for path in root.iterdir() if path.is_file() and path.name not in declared and path.name != "manifest.json"]
    warnings = [f"undeclared file ignored: {name}" for name in undeclared]
    return BundleValidation(manifest=manifest, records=records, warnings=warnings)


def import_validated_bundle(bundle: BundleValidation, session: Session, *, correction_mode: bool = False) -> dict[str, object]:
    """Persist a fully validated bundle inside the caller's transaction."""
    existing_release = session.query(DatasetRelease).filter_by(dataset_name=bundle.manifest.dataset_name, version=bundle.manifest.dataset_version).one_or_none()
    if existing_release is not None:
        return {"dataset": existing_release.dataset_name, "version": existing_release.version, "synthetic": bool((existing_release.provenance_json or {}).get("synthetic")), "publication_status": existing_release.publication_status, "rows": 0, "idempotent": True}
    if bundle.manifest.synthetic and session.bind is None:
        raise BundleError("synthetic import requires a configured PostgreSQL session")
    service = IngestionService(session)
    now = datetime.now(timezone.utc)
    def batch(operation: str, records: list[Any]) -> IngestionBatch[Any]:
        return IngestionBatch(provider=bundle.manifest.provider, operation=operation, retrieved_at=now, records=records, outcome=IngestionOutcome.SUCCEEDED, correction_mode=correction_mode)

    leagues = [NormalizedLeague.model_validate(row) for row in bundle.records.get("leagues", [])]
    service.ingest_leagues(batch("leagues", leagues))
    league = session.query(League).filter_by(code=leagues[0].code).one() if leagues else None
    if league is None:
        raise BundleError("bundle does not contain a league")
    competitions = [NormalizedCompetition.model_validate(row) for row in bundle.records.get("competitions", [])]
    service.ingest_competitions(batch("competitions", competitions), league)
    seasons = [NormalizedSeason.model_validate(row) for row in bundle.records.get("seasons", [])]
    for record in seasons:
        existing = session.query(Season).filter_by(league_id=league.id, season_code=record.season).one_or_none()
        if existing is None:
            session.add(Season(league_id=league.id, season_code=record.season, display_label=record.display_label, status=record.status, is_current=False))
    session.flush()
    teams = [NormalizedTeam.model_validate(row) for row in bundle.records.get("teams", [])]
    service.ingest_teams(batch("teams", teams), league)
    players = [NormalizedPlayer.model_validate(row) for row in bundle.records.get("players", [])]
    service.ingest_players(batch("players", players))
    games = [NormalizedGame.model_validate(row) for row in bundle.records.get("games", [])]
    service.ingest_games(batch("games", games))
    rosters = [NormalizedRosterEntry.model_validate(row) for row in bundle.records.get("rosters", [])]
    if rosters:
        service.ingest_roster_snapshots(batch("rosters", rosters))
    team_stats = [NormalizedTeamGameStats.model_validate(row) for row in bundle.records.get("team_game_stats", [])]
    if team_stats:
        service.ingest_team_game_stats(batch("team_game_stats", team_stats))
    player_stats = [NormalizedPlayerGameStats.model_validate(row) for row in bundle.records.get("player_game_stats", [])]
    if player_stats:
        service.ingest_player_game_stats(batch("player_game_stats", player_stats))
    standings = [NormalizedStandingsRow.model_validate(row) for row in bundle.records.get("standings", [])]
    if standings:
        service.ingest_standings_snapshots(batch("standings", standings))
    coverage = {"completeness": "unknown", "reason": "Expected population was not supplied by the synthetic manifest."}
    session.add(CoverageEvaluation(dataset_name=bundle.manifest.dataset_name, evaluated_at=now, included_games=len(games), expected_games=bundle.manifest.expected_games, included_entities=len(teams) + len(players), expected_entities=bundle.manifest.expected_entities, completeness_status="unknown", publication_status="withheld", blocking_reasons=["synthetic" if bundle.manifest.synthetic else "unknown_expected_population"], details=coverage, policy_version="phase2b-v1"))
    release = create_release(session, dataset_name=bundle.manifest.dataset_name, version=bundle.manifest.dataset_version, synthetic=bundle.manifest.synthetic, validation_status="passed", coverage=coverage, manifest_checksum=hashlib.sha256(json.dumps(bundle.manifest.model_dump(), sort_keys=True).encode()).hexdigest(), manifest_reference="manifest.json")
    return {"dataset": release.dataset_name, "version": release.version, "synthetic": bundle.manifest.synthetic, "publication_status": release.publication_status, "rows": sum(len(rows) for rows in bundle.records.values())}
