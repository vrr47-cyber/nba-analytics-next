import pytest

from backend.app.domain.team_scope import ACTIVE_TEAMS_FIXTURE_POLICY
from backend.app.providers.registry import ProviderConfigurationError, create_provider, create_teams_provider


def test_fixture_provider_is_registered_and_synthetic():
    provider = create_teams_provider("fixture")
    assert provider.name == "fixture"
    assert provider.synthetic is True


def test_unknown_provider_fails_at_registry_boundary():
    with pytest.raises(ProviderConfigurationError):
        create_provider("not-configured")


def test_fixture_teams_are_deterministic_and_fully_scoped():
    provider = create_teams_provider("fixture")
    first = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    second = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)

    first_league, first_teams, first_schema, first_fingerprint, first_scope = first
    second_league, second_teams, second_schema, second_fingerprint, second_scope = second
    assert first_league.source.external_id == "fixture-league"
    assert [team.source.external_id for team in first_teams] == [
        "team-redwood", "team-cinder", "team-meadow", "team-tide"
    ]
    assert len(first_teams) == first_scope.expected_count
    assert first_schema == second_schema == "fixture-teams.v1"
    assert first_fingerprint == second_fingerprint
    assert first_scope == second_scope == ACTIVE_TEAMS_FIXTURE_POLICY
    assert first_league.display_name == second_league.display_name


def test_fixture_provider_has_no_external_payload_contract():
    provider = create_teams_provider("fixture")
    _, teams, _, _, _ = provider.load_teams(ACTIVE_TEAMS_FIXTURE_POLICY)
    assert all(team.source.provider == "fixture" for team in teams)
    assert all(team.source.schema_fingerprint == "fixture-teams.v1" for team in teams)
