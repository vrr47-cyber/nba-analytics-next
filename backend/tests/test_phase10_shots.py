from datetime import datetime, timezone

import pytest

from backend.app.domain.canonical import SourceMetadata
from backend.app.domain.shots import NormalizedShot, ShotResult, ShotType, distance_bucket
from backend.app.providers.registry import create_teams_provider
from backend.app.services.shots import EXPECTED_FG_MIN_OBSERVATIONS, aggregate_shots
from backend.app.database.models import Shot
from backend.app.main import create_app


def test_fixture_shot_revisions_are_deterministic_and_synthetic():
    provider = create_teams_provider("fixture")
    first, schema, fingerprint, revision, complete = provider.load_shots("v1")
    replay, replay_schema, replay_fingerprint, replay_revision, replay_complete = provider.load_shots("v1")
    revised, _, revised_fingerprint, revised_revision, _ = provider.load_shots("v2")

    assert provider.synthetic is True
    assert complete and replay_complete
    assert first == replay
    assert schema == replay_schema == "fixture-shots.v1"
    assert revision == replay_revision == "v1"
    assert revised_revision == "v2"
    assert fingerprint == replay_fingerprint
    assert revised_fingerprint != fingerprint
    assert len({shot.provider_shot_id for shot in first}) == len(first)
    assert next(shot for shot in revised if shot.provider_shot_id == "shot-redwood-2").shot_distance != next(shot for shot in first if shot.provider_shot_id == "shot-redwood-2").shot_distance


def test_shot_contract_validates_identity_coordinates_and_point_value():
    source = SourceMetadata(provider="fixture", external_id="shot-1", retrieved_at=datetime.now(timezone.utc).isoformat())
    with pytest.raises(ValueError, match="coordinates"):
        NormalizedShot(source=source, game_external_id="game", team_external_id="team", player_external_id="player", provider_shot_id="shot-1", period=1, clock="10:00", provider_x=1, zone_version="fixture-zones.v1", zone_code="paint", shot_type=ShotType.TWO_POINT, result=ShotResult.MADE, point_value=2)
    with pytest.raises(ValueError, match="point value"):
        NormalizedShot(source=source, game_external_id="game", team_external_id="team", player_external_id="player", provider_shot_id="shot-1", period=1, clock="10:00", zone_version="fixture-zones.v1", zone_code="three", shot_type=ShotType.THREE_POINT, result=ShotResult.MADE, point_value=2)


def test_distance_buckets_are_deterministic():
    assert [distance_bucket(value) for value in (None, 3.9, 4, 9.9, 10, 15.9, 16, 23.9, 24)] == [None, "0-3", "4-9", "4-9", "10-15", "10-15", "16-23", "16-23", "24+"]


def test_shot_aggregation_returns_expected_values_only_after_threshold():
    provider = create_teams_provider("fixture")
    normalized, _, _, _, _ = provider.load_shots("v1")
    rows = [Shot(game_id=None, team_id=None, player_id=None, provider_name="fixture", provider_shot_id=shot.provider_shot_id, period=shot.period, clock=shot.clock, sequence_number=shot.sequence_number, provider_x=shot.provider_x, provider_y=shot.provider_y, normalized_x=shot.normalized_x, normalized_y=shot.normalized_y, shot_distance=shot.shot_distance, zone_version=shot.zone_version, zone_code=shot.zone_code, shot_type=shot.shot_type.value, result=shot.result.value, point_value=shot.point_value, source_run_id=None) for shot in normalized]  # type: ignore[arg-type]
    summary = aggregate_shots(rows)
    assert summary["attempts"] == len(rows)
    assert summary["actual_points"] == 9
    assert summary["expected_fg_percentage"] is None
    assert summary["expected_points"] is None
    assert EXPECTED_FG_MIN_OBSERVATIONS > len(rows)


def test_shot_api_exposes_only_the_publication_aware_bounded_contract():
    paths = create_app().openapi()["paths"]
    assert "/api/v1/shots/summary" in paths
    assert "/api/v1/shots/players/{player_id}" in paths
    assert "/api/v1/shots/zones" in paths
    assert "/api/v1/shots" not in paths
