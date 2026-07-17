import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from backend.app.database.models import Competition, CoverageEvaluation, DatasetRelease, Game, GameProviderId, League, LeagueProviderId, Player, PlayerGameStats, PlayerProviderId, RosterSnapshot, Season, SourceRun, Team, TeamGameStats, TeamProviderId
from backend.app.database.repositories.canonical import ProviderIdentityRepository, RepositoryError
from backend.app.domain.team_scope import ACTIVE_TEAMS_FIXTURE_POLICY
from backend.app.domain.player_roster_scope import ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY
from backend.app.providers.registry import create_teams_provider
from backend.app.services.bundle import import_validated_bundle, validate_bundle
from backend.app.services.box_scores import BoxScoreIngestionError, ingest_box_score_reference, validate_box_score_reference
from backend.app.services.games import GameStatusTransitionError, StructuralGameIdentityConflict, ingest_games_reference, validate_games_reference
from backend.app.services.players import ingest_players_reference
from backend.app.services.rosters import RosterIngestionError, ingest_rosters_reference
from backend.app.services.teams import ingest_teams_reference

pytestmark = pytest.mark.integration


@pytest.fixture()
def postgres_engine():
    url = os.getenv("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL is not configured")
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            connection.execute(select(1))
        yield engine
    finally:
        engine.dispose()


def test_phase2_tables_and_constraints_exist(postgres_engine):
    tables = set(inspect(postgres_engine).get_table_names())
    assert {"schema_versions", "leagues", "seasons", "games", "coverage_evaluations", "dataset_releases"} <= tables
    with Session(postgres_engine) as session:
        league = League(code="ci-fixture", display_name="CI Fixture")
        session.add(league)
        session.commit()
        assert session.scalar(select(League).where(League.code == "ci-fixture")) is not None


def test_provider_mapping_collision_and_rollback(postgres_engine):
    with Session(postgres_engine) as session:
        with session.begin():
            first = League(code="ci-collision-a", display_name="A")
            second = League(code="ci-collision-b", display_name="B")
            session.add_all([first, second])
            session.flush()
            team_a = Team(league_id=first.id, slug="a", full_name="A", short_name="A", abbreviation="A")
            team_b = Team(league_id=second.id, slug="b", full_name="B", short_name="B", abbreviation="B")
            session.add_all([team_a, team_b])
            session.flush()
            mapping = ProviderIdentityRepository(session)
            observed = datetime.now(timezone.utc)
            mapping.bind_team("ci", "same-id", team_a.id, observed)
            with pytest.raises(RepositoryError):
                mapping.bind_team("ci", "same-id", team_b.id, observed)
        assert session.scalar(select(TeamProviderId).where(TeamProviderId.external_id == "same-id")) is not None


def test_synthetic_bundle_import_release_is_withheld(postgres_engine):
    fixture = os.path.join(os.path.dirname(__file__), "fixtures", "synthetic_bundle")
    bundle = validate_bundle(fixture)
    with Session(postgres_engine) as session:
        with session.begin():
            result = import_validated_bundle(bundle, session)
            assert result["publication_status"] == "withheld"


def test_fixture_teams_ingestion_is_idempotent_and_withheld(postgres_engine):
    provider = create_teams_provider("fixture")
    league, teams, schema_version, fingerprint, scope = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    with Session(postgres_engine) as session:
        with session.begin():
            first = ingest_teams_reference(session, provider=provider.name, league=league, teams=teams, schema_version=schema_version, normalized_payload_fingerprint=fingerprint, scope_policy=scope, synthetic=provider.synthetic)
            session.flush()
            first_ids = {row.external_id: row.team_id for row in session.query(TeamProviderId).filter_by(provider_name="fixture").all()}
            second = ingest_teams_reference(session, provider=provider.name, league=league, teams=teams, schema_version=schema_version, normalized_payload_fingerprint=fingerprint, scope_policy=scope, synthetic=provider.synthetic)
            assert first["publication_status"] == second["publication_status"] == "withheld"
            assert first["rows_written"] == 4
            assert second["rows_written"] == 0
            second_ids = {row.external_id: row.team_id for row in session.query(TeamProviderId).filter_by(provider_name="fixture").all()}
            assert second_ids == first_ids
        fixture_league = session.query(League).filter_by(code="fixture-league").one()
        # The CI job imports a separate synthetic league before integration tests.
        assert session.query(Team).filter_by(league_id=fixture_league.id).count() == 4
        assert session.query(TeamProviderId).filter_by(provider_name="fixture").count() == 4
        assert session.query(LeagueProviderId).filter_by(provider_name="fixture", external_id="fixture-league").count() == 1
        runs = session.query(SourceRun).filter_by(provider_name="fixture").all()
        assert {run.metadata_json["normalized_payload_fingerprint"] for run in runs} >= {fingerprint}
        evaluations = session.query(CoverageEvaluation).filter_by(dataset_name="teams").all()
        assert all(evaluation.publication_status == "withheld" for evaluation in evaluations)
        assert session.query(DatasetRelease).filter_by(dataset_name="teams").count() == 0


def test_fixture_players_and_rosters_replay_and_revision_are_idempotent(postgres_engine):
    provider = create_teams_provider("fixture")
    league_payload, _, _, _, _ = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    players_v1, player_schema, player_fingerprint_v1, _ = provider.load_players("v1")
    rosters_v1, roster_schema, roster_fingerprint_v1, _ = provider.load_rosters("v1")
    players_v2, _, player_fingerprint_v2, _ = provider.load_players("v2")
    rosters_v2, _, roster_fingerprint_v2, _ = provider.load_rosters("v2")
    with Session(postgres_engine) as session:
        with session.begin():
            ingest_teams_reference(session, provider="fixture", league=league_payload, teams=provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)[1], schema_version="fixture-teams.v1", normalized_payload_fingerprint="phase3b-setup", scope_policy=ACTIVE_TEAMS_FIXTURE_POLICY, synthetic=True)
            league = session.query(League).filter_by(code="fixture-league").one()
            season = session.query(Season).filter_by(league_id=league.id, season_code="2099-00").one_or_none()
            if season is None:
                season = Season(league_id=league.id, season_code="2099-00", display_label="Fixture Season 2099-00", status="completed", is_current=False)
                session.add(season)
            competition = session.query(Competition).filter_by(league_id=league.id, code="regular").one_or_none()
            if competition is None:
                competition = Competition(league_id=league.id, code="regular", display_name="Fixture Regular", category="league")
                session.add(competition)
            session.flush()
            first_players = ingest_players_reference(session, provider="fixture", players=players_v1, schema_version=player_schema, normalized_payload_fingerprint=player_fingerprint_v1, synthetic=True)
            first_rosters = ingest_rosters_reference(session, provider="fixture", rosters=rosters_v1, schema_version=roster_schema, normalized_payload_fingerprint=roster_fingerprint_v1, synthetic=True)
            session.flush()
            first_player_ids = {row.external_id: row.player_id for row in session.query(PlayerProviderId).filter_by(provider_name="fixture").all()}
            first_roster_ids = {(row.season_id, row.competition_id, row.team_id, row.player_id, row.snapshot_at): row.id for row in session.query(RosterSnapshot).join(Team).filter(Team.league_id == league.id).all()}
            replay_players = ingest_players_reference(session, provider="fixture", players=players_v1, schema_version=player_schema, normalized_payload_fingerprint=player_fingerprint_v1, synthetic=True)
            replay_rosters = ingest_rosters_reference(session, provider="fixture", rosters=rosters_v1, schema_version=roster_schema, normalized_payload_fingerprint=roster_fingerprint_v1, synthetic=True)
            assert first_players["inserted"] == 4 and first_players["updated"] == 0
            assert first_rosters["inserted"] == 4 and first_rosters["updated"] == 0
            assert replay_players["inserted"] == 0 and replay_players["updated"] == 0 and replay_players["unchanged"] == 4
            assert replay_rosters["inserted"] == 0 and replay_rosters["updated"] == 0 and replay_rosters["unchanged"] == 4
            replay_player_ids = {row.external_id: row.player_id for row in session.query(PlayerProviderId).filter_by(provider_name="fixture").all()}
            assert replay_player_ids == first_player_ids
            assert {(row.season_id, row.competition_id, row.team_id, row.player_id, row.snapshot_at): row.id for row in session.query(RosterSnapshot).join(Team).filter(Team.league_id == league.id).all()} == first_roster_ids
            revised_players = ingest_players_reference(session, provider="fixture", players=players_v2, schema_version=player_schema, normalized_payload_fingerprint=player_fingerprint_v2, synthetic=True)
            revised_rosters = ingest_rosters_reference(session, provider="fixture", rosters=rosters_v2, schema_version=roster_schema, normalized_payload_fingerprint=roster_fingerprint_v2, synthetic=True)
            assert revised_players["inserted"] == 0 and revised_players["updated"] == 1
            assert revised_rosters["inserted"] == 0 and revised_rosters["updated"] == 1
            assert {row.external_id: row.player_id for row in session.query(PlayerProviderId).filter_by(provider_name="fixture").all()} == first_player_ids
            assert {(row.season_id, row.competition_id, row.team_id, row.player_id, row.snapshot_at): row.id for row in session.query(RosterSnapshot).join(Team).filter(Team.league_id == league.id).all()} == first_roster_ids
            assert session.query(Player).join(PlayerProviderId).filter(PlayerProviderId.provider_name == "fixture").count() == 4
            assert session.query(RosterSnapshot).join(Team).filter(Team.league_id == league.id).count() == 4
            assert session.query(DatasetRelease).filter(DatasetRelease.dataset_name.in_(["players", "rosters"])).count() == 0
            assert all(evaluation.publication_status == "withheld" for evaluation in session.query(CoverageEvaluation).filter(CoverageEvaluation.dataset_name.in_(["players", "rosters"])).all())


def test_roster_ingestion_requires_existing_team_mapping(postgres_engine):
    provider = create_teams_provider("fixture")
    rosters, schema_version, fingerprint, _ = provider.load_rosters("v1")
    missing_team = rosters[0].model_copy(update={"team_external_id": "team-not-mapped"})
    with Session(postgres_engine) as session:
        with session.begin():
            with pytest.raises(RosterIngestionError, match="missing canonical team mapping"):
                ingest_rosters_reference(session, provider=provider.name, rosters=(missing_team,), schema_version=schema_version, normalized_payload_fingerprint=fingerprint, scope_policy=ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY, synthetic=True)


def test_fixture_games_replay_revision_identity_and_withholding(postgres_engine):
    provider = create_teams_provider("fixture")
    league_payload, teams, team_schema, _, _ = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    games_v1, game_schema, game_fingerprint_v1, _ = provider.load_games("v1")
    games_v2, _, game_fingerprint_v2, _ = provider.load_games("v2")
    with Session(postgres_engine) as session:
        with session.begin():
            ingest_teams_reference(session, provider="fixture", league=league_payload, teams=teams, schema_version=team_schema, normalized_payload_fingerprint="phase4-setup", scope_policy=ACTIVE_TEAMS_FIXTURE_POLICY, synthetic=True)
            league = session.query(League).filter_by(code="fixture-league").one()
            season = session.query(Season).filter_by(league_id=league.id, season_code="2099-00").one_or_none()
            if season is None:
                season = Season(league_id=league.id, season_code="2099-00", display_label="Fixture Season 2099-00", status="completed", is_current=False)
                session.add(season)
            competition = session.query(Competition).filter_by(league_id=league.id, code="regular").one_or_none()
            if competition is None:
                competition = Competition(league_id=league.id, code="regular", display_name="Fixture Regular", category="league")
                session.add(competition)
            session.flush()
            first = ingest_games_reference(session, provider="fixture", games=games_v1, schema_version=game_schema, normalized_payload_fingerprint=game_fingerprint_v1, synthetic=True)
            session.flush()
            first_game_ids = {row.external_id: row.game_id for row in session.query(GameProviderId).filter_by(provider_name="fixture").all()}
            replay_validation = validate_games_reference(session, provider="fixture", games=games_v1)
            replay = ingest_games_reference(session, provider="fixture", games=games_v1, schema_version=game_schema, normalized_payload_fingerprint=game_fingerprint_v1, synthetic=True)
            revised = ingest_games_reference(session, provider="fixture", games=games_v2, schema_version=game_schema, normalized_payload_fingerprint=game_fingerprint_v2, synthetic=True)
            assert first["inserted"] == 3 and first["updated"] == 0 and first["unchanged"] == 0
            assert replay["inserted"] == 0 and replay["updated"] == 0 and replay["unchanged"] == 3
            assert revised["inserted"] == 0 and revised["updated"] == 2 and revised["unchanged"] == 1
            assert replay_validation["mutated"] is False
            assert {row.external_id: row.game_id for row in session.query(GameProviderId).filter_by(provider_name="fixture").all()} == first_game_ids
            assert session.query(Game).join(Season).filter(Season.league_id == league.id, Game.competition_id == competition.id).count() == 3
            updated_game = session.query(Game).filter_by(id=first_game_ids["game-redwood-cinder-2099"]).one()
            assert updated_game.status == "final"
            assert (updated_game.home_final_score, updated_game.away_final_score) == (101, 99)
            moved_game = session.query(Game).filter_by(id=first_game_ids["game-meadow-tide-2099"]).one()
            assert moved_game.scheduled_start.date().isoformat() == "2099-01-13"
            assert session.query(DatasetRelease).filter_by(dataset_name="games").count() == 0
            assert all(evaluation.publication_status == "withheld" for evaluation in session.query(CoverageEvaluation).filter_by(dataset_name="games").all())


def test_game_ingestion_rejects_missing_team_and_structural_conflicts(postgres_engine):
    provider = create_teams_provider("fixture")
    league_payload, teams, team_schema, _, _ = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    games, game_schema, fingerprint, _ = provider.load_games("v1")
    games_v2, _, fingerprint_v2, _ = provider.load_games("v2")
    with Session(postgres_engine) as session:
        with session.begin():
            ingest_teams_reference(session, provider="fixture", league=league_payload, teams=teams, schema_version=team_schema, normalized_payload_fingerprint="phase4-setup-errors", scope_policy=ACTIVE_TEAMS_FIXTURE_POLICY, synthetic=True)
            league = session.query(League).filter_by(code="fixture-league").one()
            season = session.query(Season).filter_by(league_id=league.id, season_code="2099-00").one_or_none()
            if season is None:
                session.add(Season(league_id=league.id, season_code="2099-00", display_label="Fixture Season 2099-00", status="completed", is_current=False))
            competition = session.query(Competition).filter_by(league_id=league.id, code="regular").one_or_none()
            if competition is None:
                session.add(Competition(league_id=league.id, code="regular", display_name="Fixture Regular", category="league"))
            session.flush()
            missing_team = games[0].model_copy(update={"home_team_external_id": "team-not-mapped"})
            with pytest.raises(ValueError, match="missing canonical home team mapping"):
                ingest_games_reference(session, provider="fixture", games=(missing_team,), schema_version=game_schema, normalized_payload_fingerprint=fingerprint, synthetic=True)
            ingest_games_reference(session, provider="fixture", games=games_v2, schema_version=game_schema, normalized_payload_fingerprint=fingerprint_v2, synthetic=True)
            structural_conflict = games[0].model_copy(update={"home_team_external_id": "team-meadow"})
            with pytest.raises(StructuralGameIdentityConflict):
                ingest_games_reference(session, provider="fixture", games=(structural_conflict,), schema_version=game_schema, normalized_payload_fingerprint=fingerprint, synthetic=True)
            with pytest.raises(GameStatusTransitionError):
                ingest_games_reference(session, provider="fixture", games=(games[0].model_copy(update={"status": "scheduled", "home_final_score": None, "away_final_score": None}),), schema_version=game_schema, normalized_payload_fingerprint=fingerprint, synthetic=True)


def test_fixture_box_score_replay_correction_and_withholding(postgres_engine):
    provider = create_teams_provider("fixture")
    league_payload, teams, team_schema, _, scope = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    players, player_schema, player_fingerprint, _ = provider.load_players("v1")
    rosters, roster_schema, roster_fingerprint, _ = provider.load_rosters("v1")
    games, game_schema, game_fingerprint, _ = provider.load_games("v2")
    payload_v1, box_schema, box_fingerprint, _ = provider.load_box_score("v1")
    payload_v2, _, box_fingerprint_v2, _ = provider.load_box_score("v2")
    with Session(postgres_engine) as session:
        with session.begin():
            ingest_teams_reference(session, provider="fixture", league=league_payload, teams=teams, schema_version=team_schema, normalized_payload_fingerprint="phase5-setup", scope_policy=scope, synthetic=True)
            league = session.scalar(select(League).where(League.code == "fixture-league"))
            assert league is not None
            season = session.scalar(select(Season).where(Season.league_id == league.id, Season.season_code == "2099-00"))
            competition = session.scalar(select(Competition).where(Competition.league_id == league.id, Competition.code == "regular"))
            assert season is not None and competition is not None
            ingest_players_reference(session, provider="fixture", players=players, schema_version=player_schema, normalized_payload_fingerprint=player_fingerprint, synthetic=True)
            ingest_rosters_reference(session, provider="fixture", rosters=rosters, schema_version=roster_schema, normalized_payload_fingerprint=roster_fingerprint, synthetic=True)
            ingest_games_reference(session, provider="fixture", games=games, schema_version=game_schema, normalized_payload_fingerprint=game_fingerprint, synthetic=True)
            first = ingest_box_score_reference(session, provider="fixture", payload=payload_v1, schema_version=box_schema, normalized_payload_fingerprint=box_fingerprint, synthetic=True)
            assert first["team_counts"] == {"inserted": 2, "updated": 0, "unchanged": 0}
            assert first["player_counts"] == {"inserted": 4, "updated": 0, "unchanged": 0}
            assert first["publication_status"] == "withheld" and first["release_created"] is False
            mapping_ids = {row.external_id: row.game_id for row in session.scalars(select(GameProviderId).where(GameProviderId.provider_name == "fixture"))}
            validation = validate_box_score_reference(session, provider="fixture", payload=payload_v1)
            replay = ingest_box_score_reference(session, provider="fixture", payload=payload_v1, schema_version=box_schema, normalized_payload_fingerprint=box_fingerprint, synthetic=True)
            assert validation["mutated"] is False
            assert replay["team_counts"] == {"inserted": 0, "updated": 0, "unchanged": 2}
            assert replay["player_counts"] == {"inserted": 0, "updated": 0, "unchanged": 4}
            with pytest.raises(BoxScoreIngestionError, match="requires correction mode"):
                ingest_box_score_reference(session, provider="fixture", payload=payload_v2, schema_version=box_schema, normalized_payload_fingerprint=box_fingerprint_v2, synthetic=True)
            corrected = ingest_box_score_reference(session, provider="fixture", payload=payload_v2, schema_version=box_schema, normalized_payload_fingerprint=box_fingerprint_v2, synthetic=True, correction_mode=True)
            assert corrected["team_counts"] == {"inserted": 0, "updated": 0, "unchanged": 2}
            assert corrected["player_counts"] == {"inserted": 0, "updated": 4, "unchanged": 0}
            assert {row.external_id: row.game_id for row in session.scalars(select(GameProviderId).where(GameProviderId.provider_name == "fixture"))} == mapping_ids
            game_id = mapping_ids["game-redwood-cinder-2099"]
            assert session.query(TeamGameStats).filter(TeamGameStats.game_id == game_id).count() == 2
            assert session.query(PlayerGameStats).filter(PlayerGameStats.game_id == game_id).count() == 4
            assert session.query(DatasetRelease).filter(DatasetRelease.dataset_name.in_(["team_game_stats", "player_game_stats"])).count() == 0
            assert all(row.publication_status == "withheld" for row in session.query(CoverageEvaluation).filter(CoverageEvaluation.dataset_name.in_(["team_game_stats", "player_game_stats"])).all())
