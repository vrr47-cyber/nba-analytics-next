from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


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
