from backend.app.domain.canonical import ParticipationStatus
from backend.app.providers.registry import create_teams_provider


def test_fixture_box_score_revisions_are_deterministic_and_synthetic():
    provider = create_teams_provider("fixture")
    first, schema, fingerprint, revision = provider.load_box_score("v1")
    replay, replay_schema, replay_fingerprint, replay_revision = provider.load_box_score("v1")
    revised, revised_schema, revised_fingerprint, revised_revision = provider.load_box_score("v2")

    assert provider.synthetic is True
    assert schema == replay_schema == revised_schema == "fixture-box-score.v1"
    assert revision == replay_revision == "v1"
    assert revised_revision == "v2"
    assert [row.model_dump(exclude={"source"}) for row in first.team_stats] == [row.model_dump(exclude={"source"}) for row in replay.team_stats]
    assert [row.model_dump(exclude={"source"}) for row in first.player_stats] == [row.model_dump(exclude={"source"}) for row in replay.player_stats]
    assert fingerprint == replay_fingerprint
    assert revised_fingerprint != fingerprint
    assert first.player_stats[-1].participation_status == ParticipationStatus.DID_NOT_PLAY
    assert first.player_stats[-1].minutes is None
    assert first.player_stats[-1].points == 0
    assert revised.player_stats[-1].participation_status == ParticipationStatus.PLAYED
    assert revised.player_stats[-1].points == 5


def test_fixture_box_score_has_complete_team_point_totals():
    payload, _, _, _ = create_teams_provider("fixture").load_box_score("v1")
    for team in payload.team_stats:
        assert sum(row.points for row in payload.player_stats if row.team_external_id == team.team_external_id) == team.points
