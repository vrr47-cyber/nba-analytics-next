from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from sqlalchemy.orm import Session

from backend.app.database.models import CoverageEvaluation, League, SourceRun, Team, TeamProviderId
from backend.app.database.repositories.canonical import ProviderIdentityRepository
from backend.app.domain.canonical import NormalizedLeague, NormalizedTeam
from backend.app.domain.team_scope import TeamScopePolicy


class TeamsIngestionError(ValueError):
    pass


def ingest_teams_reference(
    session: Session,
    *,
    provider: str,
    league: NormalizedLeague,
    teams: tuple[NormalizedTeam, ...],
    schema_version: str,
    normalized_payload_fingerprint: str,
    scope_policy: TeamScopePolicy,
    synthetic: bool,
) -> dict[str, Any]:
    loaded_at = datetime.now(timezone.utc)
    source_run = SourceRun(
        id=uuid4(),
        provider_name=provider,
        status="running",
        started_at=loaded_at,
        metadata_json={
            "operation": "teams",
            "load_timestamp": loaded_at.isoformat(),
            "schema_version": schema_version,
            "record_count": len(teams),
            "normalized_payload_fingerprint": normalized_payload_fingerprint,
            "scope_policy_version": scope_policy.policy_version,
            "synthetic": synthetic,
        },
    )
    session.add(source_run)
    try:
        if league.source.provider != provider:
            raise TeamsIngestionError("league provider does not match teams provider")
        provider_ids = [team.source.external_id for team in teams]
        if len(provider_ids) != len(set(provider_ids)):
            raise TeamsIngestionError("duplicate provider team IDs in teams response")
        canonical_keys = [team.slug for team in teams]
        if len(canonical_keys) != len(set(canonical_keys)):
            raise TeamsIngestionError("duplicate canonical team keys in teams response")
        if league.source.external_id not in scope_policy.eligible_league_external_ids:
            raise TeamsIngestionError("league is outside the active teams scope policy")
        if len(teams) != scope_policy.expected_count:
            completeness = "partial"
            blocking_reasons = ["team population does not match the versioned scope policy"]
        else:
            completeness = "complete"
            blocking_reasons = []
        canonical_league = session.query(League).filter_by(code=league.code).one_or_none()
        if canonical_league is None:
            canonical_league = League(code=league.code, display_name=league.display_name)
            session.add(canonical_league)
            session.flush()
        else:
            canonical_league.display_name = league.display_name
        identities = ProviderIdentityRepository(session)
        identities.bind_league(provider, league.source.external_id, canonical_league.id, loaded_at)
        written = 0
        for record in teams:
            if record.league_code != league.code:
                raise TeamsIngestionError(f"team {record.source.external_id} references another league")
            provider_mapping = session.query(TeamProviderId).filter_by(provider_name=provider, external_id=record.source.external_id).one_or_none()
            canonical_team = session.get(Team, provider_mapping.team_id) if provider_mapping else None
            if canonical_team is None:
                canonical_team = session.query(Team).filter_by(league_id=canonical_league.id, slug=record.slug).one_or_none()
            if canonical_team is None:
                canonical_team = Team(league_id=canonical_league.id, slug=record.slug, full_name=record.full_name, short_name=record.short_name, abbreviation=record.abbreviation, city=record.city)
                session.add(canonical_team)
                session.flush()
                written += 1
            else:
                canonical_team.full_name = record.full_name
                canonical_team.short_name = record.short_name
                canonical_team.abbreviation = record.abbreviation
                if record.city is not None:
                    canonical_team.city = record.city
            identities.bind_team(provider, record.source.external_id, canonical_team.id, loaded_at)
        source_run.status = "succeeded"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_written": written}
        session.add(CoverageEvaluation(dataset_name="teams", league_id=canonical_league.id, evaluated_at=source_run.completed_at, included_games=0, expected_games=None, included_entities=len(teams), expected_entities=scope_policy.expected_count, coverage_ratio=(len(teams) / scope_policy.expected_count if scope_policy.expected_count else None), completeness_status=completeness, publication_status="withheld", blocking_reasons=blocking_reasons + (["synthetic_fixture"] if synthetic else []), details={"scope": scope_policy.scope, "provider": provider, "source_run_id": str(source_run.id)}, policy_version=scope_policy.policy_version))
        return {"source_run_id": str(source_run.id), "rows_received": len(teams), "rows_written": written, "coverage_status": completeness, "publication_status": "withheld", "synthetic": synthetic}
    except Exception as exc:
        source_run.status = "failed"
        source_run.completed_at = datetime.now(timezone.utc)
        source_run.error_message = str(exc)
        source_run.metadata_json = {**(source_run.metadata_json or {}), "rows_written": 0}
        session.flush()
        raise
