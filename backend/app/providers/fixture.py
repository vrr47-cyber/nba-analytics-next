from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone

from backend.app.domain.box_scores import NormalizedBoxScorePayload
from backend.app.domain.canonical import BoxScoreLine, CompetitionCode, GameStatus, NormalizedGame, NormalizedLeague, NormalizedPlayer, NormalizedPlayerGameStats, NormalizedRosterEntry, NormalizedTeam, NormalizedTeamGameStats, ParticipationStatus, SourceMetadata
from backend.app.domain.team_scope import ACTIVE_TEAMS_FIXTURE_POLICY, TeamScopePolicy
from backend.app.providers.dto import FixtureBoxScoreDTO, FixtureGameDTO, FixtureGamesDTO, FixturePlayerDTO, FixturePlayersDTO, FixtureRosterDTO, FixtureRostersDTO, FixtureTeamDTO, FixtureTeamsDTO, FixturePlayerStatDTO, FixtureTeamStatDTO


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
                FixturePlayerDTO(provider_player_id="player-ember", slug="ember-vale", full_name="Ember Vale", first_name="Ember", last_name="Vale", position=mutable_position, birth_date=date(2090, 1, 1)),
                FixturePlayerDTO(provider_player_id="player-ash", slug="ash-rowan", full_name="Ash Rowan", first_name="Ash", last_name="Rowan", position="C", birth_date=date(2089, 2, 2)),
                FixturePlayerDTO(provider_player_id="player-flint", slug="flint-moss", full_name="Flint Moss", first_name="Flint", last_name="Moss", position="G", birth_date=date(2091, 3, 3)),
                FixturePlayerDTO(provider_player_id="player-river", slug="river-sage", full_name="River Sage", first_name="River", last_name="Sage", position="F", birth_date=date(2090, 4, 4)),
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
                FixtureRosterDTO(provider_roster_id="roster-redwood-ember-2099", provider_team_id="team-redwood", provider_player_id="player-ember", season="2099-00", competition_code="regular", snapshot_at=datetime(2099, 1, 2, tzinfo=timezone.utc), roster_status=ember_status, jersey_number="7", listed_position="F"),
                FixtureRosterDTO(provider_roster_id="roster-redwood-ash-2099", provider_team_id="team-redwood", provider_player_id="player-ash", season="2099-00", competition_code="regular", snapshot_at=datetime(2099, 1, 2, tzinfo=timezone.utc), roster_status="active", jersey_number="12", listed_position="C"),
                FixtureRosterDTO(provider_roster_id="roster-cinder-flint-2099", provider_team_id="team-cinder", provider_player_id="player-flint", season="2099-00", competition_code="regular", snapshot_at=datetime(2099, 1, 2, tzinfo=timezone.utc), roster_status="active", jersey_number="3", listed_position="G"),
                FixtureRosterDTO(provider_roster_id="roster-cinder-river-2099", provider_team_id="team-cinder", provider_player_id="player-river", season="2099-00", competition_code="regular", snapshot_at=datetime(2099, 1, 2, tzinfo=timezone.utc), roster_status="active", jersey_number="21", listed_position="F"),
            ),
        )
        serialized = json.dumps(payload.model_dump(mode="json", exclude={"loaded_at"}), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        records = tuple(
            NormalizedRosterEntry(
                source=SourceMetadata(provider=self.name, external_id=roster.provider_roster_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version),
                season=roster.season, competition_code=CompetitionCode(roster.competition_code), team_external_id=roster.provider_team_id,
                player_external_id=roster.provider_player_id, snapshot_at=roster.snapshot_at.isoformat(), jersey_number=roster.jersey_number,
                listed_position=roster.listed_position, roster_status=roster.roster_status,
            )
            for roster in payload.rosters
        )
        return records, payload.schema_version, fingerprint, payload.revision

    def load_games(self, revision: str = "v1") -> tuple[tuple[NormalizedGame, ...], str, str, str]:
        loaded_at = datetime.now(timezone.utc)
        redwood_cinder_start = datetime(2099, 1, 10, 19, tzinfo=timezone.utc)
        meadow_tide_start = datetime(2099, 1, 13 if revision == "v2" else 11, 19, tzinfo=timezone.utc)
        payload = FixtureGamesDTO(
            schema_version="fixture-games.v1",
            revision=revision,
            loaded_at=loaded_at,
            games=(
                FixtureGameDTO(provider_game_id="game-redwood-cinder-2099", season="2099-00", competition_code="regular", home_provider_team_id="team-redwood", away_provider_team_id="team-cinder", scheduled_start=redwood_cinder_start, status="final" if revision == "v2" else "scheduled", home_final_score=101 if revision == "v2" else None, away_final_score=99 if revision == "v2" else None),
                FixtureGameDTO(provider_game_id="game-meadow-tide-2099", season="2099-00", competition_code="regular", home_provider_team_id="team-meadow", away_provider_team_id="team-tide", scheduled_start=meadow_tide_start, status="postponed"),
                FixtureGameDTO(provider_game_id="game-redwood-meadow-2099", season="2099-00", competition_code="regular", home_provider_team_id="team-redwood", away_provider_team_id="team-meadow", scheduled_start=datetime(2099, 1, 12, 19, tzinfo=timezone.utc), status="final", home_final_score=100, away_final_score=95, neutral_site=True),
            ),
        )
        serialized = json.dumps(payload.model_dump(mode="json", exclude={"loaded_at"}), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        records = tuple(
            NormalizedGame(
                source=SourceMetadata(provider=self.name, external_id=game.provider_game_id, retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version),
                season=game.season, competition_code=CompetitionCode(game.competition_code), scheduled_start=game.scheduled_start.isoformat(),
                game_date=game.scheduled_start.astimezone(timezone.utc).date().isoformat(), home_team_external_id=game.home_provider_team_id,
                away_team_external_id=game.away_provider_team_id, status=GameStatus(game.status), home_final_score=game.home_final_score,
                away_final_score=game.away_final_score, neutral_site=game.neutral_site, official_external_url=game.official_external_url,
                archival_external_url=game.archival_external_url,
            )
            for game in payload.games
        )
        return records, payload.schema_version, fingerprint, payload.revision

    def load_box_score(self, revision: str = "v1") -> tuple[NormalizedBoxScorePayload, str, str, str]:
        loaded_at = datetime.now(timezone.utc)
        river_status = "played" if revision == "v2" else "did_not_play"
        river_minutes = "08:00" if revision == "v2" else None
        payload = FixtureBoxScoreDTO(
            schema_version="fixture-box-score.v1", revision=revision, loaded_at=loaded_at,
            provider_game_id="game-redwood-cinder-2099", complete_roster_coverage=True,
            team_stats=(
                FixtureTeamStatDTO(provider_team_id="team-redwood", opponent_provider_team_id="team-cinder", home_away="home", result="W", minutes="48:00", points=101, field_goals_made=38, field_goals_attempted=85, three_pointers_made=12, three_pointers_attempted=35, free_throws_made=13, free_throws_attempted=17, offensive_rebounds=10, defensive_rebounds=30, total_rebounds=40, assists=24, steals=7, blocks=5, turnovers=11, personal_fouls=18, plus_minus=2),
                FixtureTeamStatDTO(provider_team_id="team-cinder", opponent_provider_team_id="team-redwood", home_away="away", result="L", minutes="48:00", points=99, field_goals_made=37, field_goals_attempted=84, three_pointers_made=11, three_pointers_attempted=34, free_throws_made=14, free_throws_attempted=18, offensive_rebounds=9, defensive_rebounds=28, total_rebounds=37, assists=22, steals=6, blocks=4, turnovers=13, personal_fouls=20, plus_minus=-2),
            ),
            player_stats=(
                FixturePlayerStatDTO(provider_team_id="team-redwood", opponent_provider_team_id="team-cinder", home_away="home", result="W", minutes="48:00", points=56 if revision == "v2" else 55, field_goals_made=20, field_goals_attempted=35, three_pointers_made=6, three_pointers_attempted=13, free_throws_made=10, free_throws_attempted=12, offensive_rebounds=3, defensive_rebounds=8, total_rebounds=11, assists=7, steals=2, blocks=1, turnovers=3, personal_fouls=2, plus_minus=4, provider_player_id="player-ember", starter=True, participation_status="played", player_minutes="35:00"),
                FixturePlayerStatDTO(provider_team_id="team-redwood", opponent_provider_team_id="team-cinder", home_away="home", result="W", minutes="48:00", points=45 if revision == "v2" else 46, field_goals_made=18, field_goals_attempted=39, three_pointers_made=6, three_pointers_attempted=16, free_throws_made=3, free_throws_attempted=5, offensive_rebounds=7, defensive_rebounds=10, total_rebounds=17, assists=9, steals=1, blocks=2, turnovers=4, personal_fouls=3, plus_minus=-2, provider_player_id="player-ash", starter=False, participation_status="played", player_minutes="28:00"),
                FixturePlayerStatDTO(provider_team_id="team-cinder", opponent_provider_team_id="team-redwood", home_away="away", result="L", minutes="48:00", points=94 if revision == "v2" else 99, field_goals_made=35, field_goals_attempted=78, three_pointers_made=10, three_pointers_attempted=30, free_throws_made=14, free_throws_attempted=18, offensive_rebounds=6, defensive_rebounds=16, total_rebounds=22, assists=12, steals=3, blocks=2, turnovers=8, personal_fouls=3, plus_minus=-1, provider_player_id="player-flint", starter=True, participation_status="played", player_minutes="37:00"),
                FixturePlayerStatDTO(provider_team_id="team-cinder", opponent_provider_team_id="team-redwood", home_away="away", result="L", minutes="48:00", points=5 if revision == "v2" else 0, field_goals_made=2 if revision == "v2" else 0, field_goals_attempted=5 if revision == "v2" else 0, three_pointers_made=1 if revision == "v2" else 0, three_pointers_attempted=2 if revision == "v2" else 0, free_throws_made=0, free_throws_attempted=0, offensive_rebounds=1 if revision == "v2" else 0, defensive_rebounds=0, total_rebounds=1 if revision == "v2" else 0, assists=2 if revision == "v2" else 0, steals=1 if revision == "v2" else 0, blocks=0, turnovers=1 if revision == "v2" else 0, personal_fouls=1 if revision == "v2" else 0, plus_minus=0 if revision == "v2" else None, provider_player_id="player-river", starter=False, participation_status=river_status, status_comment=None if revision == "v2" else "coach decision", player_minutes=river_minutes),
            ),
        )
        serialized = json.dumps(payload.model_dump(mode="json", exclude={"loaded_at"}), sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized.encode()).hexdigest()
        def line_kwargs(row: FixtureTeamStatDTO) -> dict[str, object]:
            return {key: getattr(row, key) for key in BoxScoreLine.model_fields}
        teams = tuple(NormalizedTeamGameStats(source=SourceMetadata(provider=self.name, external_id=f"{payload.provider_game_id}:{row.provider_team_id}", retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version), game_external_id=payload.provider_game_id, team_external_id=row.provider_team_id, opponent_external_id=row.opponent_provider_team_id, home_away=row.home_away, result=row.result, minutes=row.minutes, **line_kwargs(row)) for row in payload.team_stats)
        players = tuple(NormalizedPlayerGameStats(source=SourceMetadata(provider=self.name, external_id=f"{payload.provider_game_id}:{row.provider_player_id}", retrieved_at=loaded_at.isoformat(), schema_fingerprint=payload.schema_version), game_external_id=payload.provider_game_id, player_external_id=row.provider_player_id, team_external_id=row.provider_team_id, starter=row.starter, participation_status=ParticipationStatus(row.participation_status), status_comment=row.status_comment, minutes=row.player_minutes, **line_kwargs(row)) for row in payload.player_stats)
        return NormalizedBoxScorePayload(game_external_id=payload.provider_game_id, team_stats=teams, player_stats=players, complete_roster_coverage=payload.complete_roster_coverage), payload.schema_version, fingerprint, payload.revision
