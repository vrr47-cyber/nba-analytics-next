from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from backend.app.domain.canonical import NormalizedLeague, NormalizedTeam, SourceMetadata
from backend.app.domain.team_scope import ACTIVE_TEAMS_FIXTURE_POLICY, TeamScopePolicy
from backend.app.providers.dto import FixtureTeamDTO, FixtureTeamsDTO


class FixtureTeamsProvider:
    """Deterministic, fictional, no-network reference provider for Phase 3A."""

    name = "fixture"
    synthetic = True

    def load_teams(self, scope: TeamScopePolicy = ACTIVE_TEAMS_FIXTURE_POLICY) -> tuple[NormalizedLeague, tuple[NormalizedTeam, ...], str, str, TeamScopePolicy]:
        loaded_at = datetime.now(timezone.utc)
        payload = FixtureTeamsDTO(
            schema_version="fixture-teams.v1",
            provider_league_id="fixture-league",
            league_code="fixture-league",
            league_name="Fixture League",
            loaded_at=loaded_at,
            teams=(
                FixtureTeamDTO(provider_team_id="team-redwood", slug="redwood", full_name="Redwood", short_name="Redwood", abbreviation="RWD"),
                FixtureTeamDTO(provider_team_id="team-cinder", slug="cinder", full_name="Cinder", short_name="Cinder", abbreviation="CND"),
                FixtureTeamDTO(provider_team_id="team-meadow", slug="meadow", full_name="Meadow", short_name="Meadow", abbreviation="MDW"),
                FixtureTeamDTO(provider_team_id="team-tide", slug="tide", full_name="Tide", short_name="Tide", abbreviation="TDE"),
            ),
        )
        serialized = json.dumps(payload.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        league_source = SourceMetadata(provider=self.name, external_id=payload.provider_league_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version)
        league = NormalizedLeague(source=league_source, code=payload.league_code, display_name=payload.league_name)
        teams = tuple(NormalizedTeam(source=SourceMetadata(provider=self.name, external_id=team.provider_team_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version), league_code=payload.league_code, slug=team.slug, full_name=team.full_name, short_name=team.short_name, abbreviation=team.abbreviation, city=team.city) for team in payload.teams)
        return league, teams, payload.schema_version, fingerprint, scope
