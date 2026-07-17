from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, CoverageEvaluation, Player, PlayerProviderId, RosterSnapshot, Season, SourceRun, Team, TeamProviderId
from backend.app.domain.player_roster_scope import ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY, PlayerRosterScopePolicy
from backend.app.domain.canonical import NormalizedRosterEntry


class RosterIngestionError(ValueError):
    pass


def ingest_rosters_reference(
    session: Session,
    *,
    provider: str,
    rosters: tuple[NormalizedRosterEntry, ...],
    schema_version: str,
    normalized_payload_fingerprint: str,
    scope_policy: PlayerRosterScopePolicy = ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY,
    synthetic: bool,
) -> dict[str, Any]:
    loaded_at = datetime.now(timezone.utc)
    source_run = SourceRun(id=uuid4(), provider_name=provider, status="running", started_at=loaded_at, metadata_json={"operation": "rosters", "load_timestamp": loaded_at.isoformat(), "schema_version": schema_version, "record_count": len(rosters), "normalized_payload_fingerprint": normalized_payload_fingerprint, "scope_policy_version": scope_policy.policy_version, "synthetic": synthetic})
    session.add(source_run)
    try:
        roster_ids = [roster.source.external_id for roster in rosters]
        if len(roster_ids) != len(set(roster_ids)):
            raise RosterIngestionError("duplicate provider roster IDs in roster response")
        inserted = updated = unchanged = 0
        for record in rosters:
            team_mapping = session.scalar(select(TeamProviderId).where(TeamProviderId.provider_name == provider, TeamProviderId.external_id == record.team_external_id))
            if team_mapping is None:
                raise RosterIngestionError(f"missing canonical team mapping: {provider}/{record.team_external_id}")
            team = session.get(Team, team_mapping.team_id)
            if team is None:
                raise RosterIngestionError(f"canonical team mapping points to missing team: {provider}/{record.team_external_id}")
            player_mapping = session.scalar(select(PlayerProviderId).where(PlayerProviderId.provider_name == provider, PlayerProviderId.external_id == record.player_external_id))
            if player_mapping is None:
                raise RosterIngestionError(f"missing canonical player mapping: {provider}/{record.player_external_id}")
            player = session.get(Player, player_mapping.player_id)
            if player is None:
                raise RosterIngestionError(f"canonical player mapping points to missing player: {provider}/{record.player_external_id}")
            season = session.scalar(select(Season).where(Season.league_id == team.league_id, Season.season_code == record.season))
            if season is None:
                raise RosterIngestionError(f"missing canonical season: league={team.league_id} season={record.season}")
            competition = session.scalar(select(Competition).where(Competition.league_id == team.league_id, Competition.code == record.competition_code))
            if competition is None:
                raise RosterIngestionError(f"missing canonical competition: league={team.league_id} competition={record.competition_code}")
            snapshot_at = datetime.fromisoformat(record.snapshot_at)
            existing = session.scalar(select(RosterSnapshot).where(RosterSnapshot.season_id == season.id, RosterSnapshot.competition_id == competition.id, RosterSnapshot.team_id == team.id, RosterSnapshot.player_id == player.id, RosterSnapshot.snapshot_at == snapshot_at))
            if existing is None:
                session.add(RosterSnapshot(season_id=season.id, competition_id=competition.id, team_id=team.id, player_id=player.id, snapshot_at=snapshot_at, jersey_number=record.jersey_number, listed_position=record.listed_position, roster_status=record.roster_status, source_run_id=source_run.id))
                inserted += 1
            else:
                values = {"jersey_number": record.jersey_number, "listed_position": record.listed_position, "roster_status": record.roster_status}
                changed = any(getattr(existing, key) != value for key, value in values.items())
                for key, value in values.items():
                    setattr(existing, key, value)
                existing.source_run_id = source_run.id
                if changed:
                    updated += 1
                else:
                    unchanged += 1
        completed_at = datetime.now(timezone.utc)
        source_run.status = "succeeded"
        source_run.completed_at = completed_at
        source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_inserted": inserted, "rows_updated": updated, "rows_unchanged": unchanged}
        completeness = "complete" if len(rosters) == scope_policy.expected_roster_count else "partial"
        blocking = ([] if completeness == "complete" else ["roster population does not match the versioned scope policy"]) + (["synthetic_fixture"] if synthetic else [])
        session.add(CoverageEvaluation(dataset_name="rosters", evaluated_at=completed_at, included_games=0, expected_games=None, included_entities=len(rosters), expected_entities=scope_policy.expected_roster_count, coverage_ratio=(len(rosters) / scope_policy.expected_roster_count if scope_policy.expected_roster_count else None), completeness_status=completeness, publication_status="withheld", blocking_reasons=blocking, details={"scope": scope_policy.roster_scope, "provider": provider, "source_run_id": str(source_run.id), "snapshot_behavior": "stable_membership_row"}, policy_version=scope_policy.policy_version))
        return {"source_run_id": str(source_run.id), "rows_received": len(rosters), "inserted": inserted, "updated": updated, "unchanged": unchanged, "withheld": len(rosters), "publication_status": "withheld", "synthetic": synthetic}
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_inserted": 0, "rows_updated": 0, "rows_unchanged": 0}
        session.flush()
        raise
