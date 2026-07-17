from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import CoverageEvaluation, Player, PlayerProviderId, SourceRun
from backend.app.database.repositories.canonical import ProviderIdentityRepository
from backend.app.domain.canonical import NormalizedPlayer
from backend.app.domain.player_roster_scope import ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY, PlayerRosterScopePolicy


class PlayerIngestionError(ValueError):
    pass


def ingest_players_reference(
    session: Session,
    *,
    provider: str,
    players: tuple[NormalizedPlayer, ...],
    schema_version: str,
    normalized_payload_fingerprint: str,
    scope_policy: PlayerRosterScopePolicy = ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY,
    synthetic: bool,
) -> dict[str, Any]:
    loaded_at = datetime.now(timezone.utc)
    source_run = SourceRun(id=uuid4(), provider_name=provider, status="running", started_at=loaded_at, metadata_json={"operation": "players", "load_timestamp": loaded_at.isoformat(), "schema_version": schema_version, "record_count": len(players), "normalized_payload_fingerprint": normalized_payload_fingerprint, "scope_policy_version": scope_policy.policy_version, "synthetic": synthetic})
    session.add(source_run)
    try:
        provider_ids = [player.source.external_id for player in players]
        if len(provider_ids) != len(set(provider_ids)):
            raise PlayerIngestionError("duplicate provider player IDs in players response")
        inserted = updated = unchanged = 0
        identities = ProviderIdentityRepository(session)
        for record in players:
            mapping = session.scalar(select(PlayerProviderId).where(PlayerProviderId.provider_name == provider, PlayerProviderId.external_id == record.source.external_id))
            player = session.get(Player, mapping.player_id) if mapping else None
            if player is None:
                # No provider-independent stable player key exists. Never match by slug or biography.
                player = Player(slug=record.slug, full_name=record.full_name, first_name=record.first_name, last_name=record.last_name, position=record.position, active=record.active, birth_date=date.fromisoformat(record.birth_date) if record.birth_date else None)
                session.add(player)
                session.flush()
                inserted += 1
            else:
                values = {"full_name": record.full_name, "first_name": record.first_name, "last_name": record.last_name, "position": record.position, "active": record.active, "birth_date": date.fromisoformat(record.birth_date) if record.birth_date else None}
                changed = any(getattr(player, key) != value for key, value in values.items())
                for key, value in values.items():
                    setattr(player, key, value)
                if changed:
                    updated += 1
                else:
                    unchanged += 1
            identities.bind_player(provider, record.source.external_id, player.id, datetime.fromisoformat(record.source.retrieved_at))
        completed_at = datetime.now(timezone.utc)
        source_run.status = "succeeded"
        source_run.completed_at = completed_at
        source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_inserted": inserted, "rows_updated": updated, "rows_unchanged": unchanged}
        completeness = "complete" if len(players) == scope_policy.expected_player_count else "partial"
        blocking = ([] if completeness == "complete" else ["player population does not match the versioned scope policy"]) + (["synthetic_fixture"] if synthetic else [])
        session.add(CoverageEvaluation(dataset_name="players", evaluated_at=completed_at, included_games=0, expected_games=None, included_entities=len(players), expected_entities=scope_policy.expected_player_count, coverage_ratio=(len(players) / scope_policy.expected_player_count if scope_policy.expected_player_count else None), completeness_status=completeness, publication_status="withheld", blocking_reasons=blocking, details={"scope": scope_policy.player_scope, "provider": provider, "source_run_id": str(source_run.id)}, policy_version=scope_policy.policy_version))
        return {"source_run_id": str(source_run.id), "rows_received": len(players), "inserted": inserted, "updated": updated, "unchanged": unchanged, "withheld": len(players), "publication_status": "withheld", "synthetic": synthetic}
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_inserted": 0, "rows_updated": 0, "rows_unchanged": 0}
        session.flush()
        raise
