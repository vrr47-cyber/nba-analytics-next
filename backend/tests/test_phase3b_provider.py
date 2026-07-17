import pytest
from pydantic import ValidationError

from backend.app.domain.player_roster_scope import ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY
from backend.app.providers.dto import FixturePlayerDTO
from backend.app.providers.registry import create_teams_provider


def test_fixture_player_and_roster_loading_is_explicitly_revisioned():
    provider = create_teams_provider("fixture")
    players_v1, player_schema, player_fingerprint_v1, revision_v1 = provider.load_players("v1")
    players_v1_replay, _, player_fingerprint_replay, _ = provider.load_players("v1")
    players_v2, _, player_fingerprint_v2, revision_v2 = provider.load_players("v2")
    rosters_v1, roster_schema, roster_fingerprint_v1, _ = provider.load_rosters("v1")
    rosters_v2, _, roster_fingerprint_v2, _ = provider.load_rosters("v2")

    assert len(players_v1) == ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY.expected_player_count
    assert len(rosters_v1) == ACTIVE_FIXTURE_PLAYER_ROSTER_POLICY.expected_roster_count
    assert player_schema == "fixture-players.v1"
    assert roster_schema == "fixture-rosters.v1"
    assert revision_v1 == "v1"
    assert revision_v2 == "v2"
    assert player_fingerprint_v1 == player_fingerprint_replay
    assert roster_fingerprint_v1 != roster_fingerprint_v2
    assert player_fingerprint_v1 != player_fingerprint_v2
    assert players_v1[0].position != players_v2[0].position
    assert rosters_v1[0].roster_status != rosters_v2[0].roster_status
    assert [player.source.external_id for player in players_v1] == [player.source.external_id for player in players_v1_replay]
    assert all(player.source.provider == "fixture" for player in players_v1)


def test_fixture_player_dto_rejects_missing_provider_identity():
    with pytest.raises(ValidationError):
        FixturePlayerDTO(provider_player_id="", slug="fixture", full_name="Fixture")
