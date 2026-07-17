from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from backend.app.domain.canonical import NormalizedLeague, NormalizedPlayer, NormalizedRosterEntry, NormalizedTeam, SourceMetadata
from backend.app.domain.team_scope import ACTIVE_TEAMS_FIXTURE_POLICY, TeamScopePolicy
from backend.app.providers.dto import FixturePlayerDTO, FixturePlayersDTO, FixtureRosterDTO, FixtureRostersDTO, FixtureTeamDTO, FixtureTeamsDTO


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
        serialized = json.dumps(payload.model_dump(mode="json", exclude={"loaded_at"}), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        league_source = SourceMetadata(provider=self.name, external_id=payload.provider_league_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version)
        league = NormalizedLeague(source=league_source, code=payload.league_code, display_name=payload.league_name)
        teams = tuple(NormalizedTeam(source=SourceMetadata(provider=self.name, external_id=team.provider_team_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version), league_code=payload.league_code, slug=team.slug, full_name=team.full_name, short_name=team.short_name, abbreviation=team.abbreviation, city=team.city) for team in payload.teams)
        return league, teams, payload.schema_version, fingerprint, scope

    def load_players(self, revision: str = "v1") -> tuple[tuple[NormalizedPlayer, ...], str, str, str]:
        loaded_at = datetime.now(timezone.utc)
        mutable_position = "F" if revision == "v2" else "G"
        payload = FixturePlayersDTO(
            schema_version="fixture-players.v1",
            revision=revision,
            loaded_at=loaded_at,
            players=(
                FixturePlayerDTO(provider_player_id="player-ember", slug="ember-vale", full_name="Ember Vale", first_name="Ember", last_name="Vale", position=mutable_position, birth_date="2090-01-01"),
                FixturePlayerDTO(provider_player_id="player-ash", slug="ash-rowan", full_name="Ash Rowan", first_name="Ash", last_name="Rowan", position="C", birth_date="2089-02-02"),
                FixturePlayerDTO(provider_player_id="player-flint", slug="flint-moss", full_name="Flint Moss", first_name="Flint", last_name="Moss", position="G", birth_date="2091-03-03"),
                FixturePlayerDTO(provider_player_id="player-river", slug="river-sage", full_name="River Sage", first_name="River", last_name="Sage", position="F", birth_date="2090-04-04"),
            ),
        )
        serialized = json.dumps(payload.model_dump(mode="json", exclude={"loaded_at"}), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        records = tuple(
            NormalizedPlayer(
                source=SourceMetadata(provider=self.name, external_id=player.provider_player_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version),
                slug=player.slug, full_name=player.full_name, first_name=player.first_name, last_name=player.last_name,
                position=player.position, active=player.active, birth_date=player.birth_date.isoformat() if player.birth_date else None,
            )
            for player in payload.players
        )
        return records, payload.schema_version, fingerprint, payload.revision

    def load_rosters(self, revision: str = "v1") -> tuple[tuple[NormalizedRosterEntry, ...], str, str, str]:
        loaded_at = datetime.now(timezone.utc)
        ember_status = "inactive" if revision == "v2" else "active"
        payload = FixtureRostersDTO(
            schema_version="fixture-rosters.v1",
            revision=revision,
            loaded_at=loaded_at,
            rosters=(
                FixtureRosterDTO(provider_roster_id="roster-redwood-ember-2099", provider_team_id="team-redwood", provider_player_id="player-ember", season="2099-00", competition_code="regular", snapshot_at="2099-01-02T00:00:00+00:00", roster_status=ember_status, jersey_number="7", listed_position="F"),
                FixtureRosterDTO(provider_roster_id="roster-redwood-ash-2099", provider_team_id="team-redwood", provider_player_id="player-ash", season="2099-00", competition_code="regular", snapshot_at="2099-01-02T00:00:00+00:00", roster_status="active", jersey_number="12", listed_position="C"),
                FixtureRosterDTO(provider_roster_id="roster-cinder-flint-2099", provider_team_id="team-cinder", provider_player_id="player-flint", season="2099-00", competition_code="regular", snapshot_at="2099-01-02T00:00:00+00:00", roster_status="active", jersey_number="3", listed_position="G"),
                FixtureRosterDTO(provider_roster_id="roster-cinder-river-2099", provider_team_id="team-cinder", provider_player_id="player-river", season="2099-00", competition_code="regular", snapshot_at="2099-01-02T00:00:00+00:00", roster_status="active", jersey_number="21", listed_position="F"),
            ),
        )
        serialized = json.dumps(payload.model_dump(mode="json", exclude={"loaded_at"}), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        records = tuple(
            NormalizedRosterEntry(
                source=SourceMetadata(provider=self.name, external_id=roster.provider_roster_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version),
                season=roster.season, competition_code=roster.competition_code, team_external_id=roster.provider_team_id,
                player_external_id=roster.provider_player_id, snapshot_at=roster.snapshot_at.isoformat(), jersey_number=roster.jersey_number,
                listed_position=roster.listed_position, roster_status=roster.roster_status,
            )
            for roster in payload.rosters
        )
        return records, payload.schema_version, fingerprint, payload.revision
