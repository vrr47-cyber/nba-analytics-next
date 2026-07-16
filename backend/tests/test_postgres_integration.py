import os
from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.orm import Session

from backend.app.database.models import League, Team, TeamProviderId
from backend.app.database.repositories.canonical import ProviderIdentityRepository, RepositoryError
from backend.app.services.bundle import import_validated_bundle, validate_bundle

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
