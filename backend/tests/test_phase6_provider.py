import pytest
from pydantic import ValidationError

from backend.app.domain.play_by_play import NormalizedEventParticipant, ParticipantRole
from backend.app.providers.registry import create_teams_provider


def test_fixture_play_by_play_revisions_are_deterministic_and_reorderable():
    provider = create_teams_provider("fixture")
    first, schema, fingerprint, revision = provider.load_play_by_play("v1")
    replay, replay_schema, replay_fingerprint, replay_revision = provider.load_play_by_play("v1")
    revised, _, revised_fingerprint, revised_revision = provider.load_play_by_play("v2")
    reordered = first.model_copy(update={"events": tuple(reversed(first.events))})

    assert provider.synthetic is True
    assert schema == replay_schema == "fixture-play-by-play.v1"
    assert revision == replay_revision == "v1"
    assert revised_revision == "v2"
    assert fingerprint == replay_fingerprint
    assert revised_fingerprint != fingerprint
    assert first.events[-1].home_score == revised.events[-1].home_score == 101
    assert first.events[-1].away_score == revised.events[-1].away_score == 99
    assert {event.provider_event_id for event in first.events} != {event.provider_event_id for event in revised.events}
    assert [event.provider_event_id for event in sorted(reordered.events, key=lambda item: item.sequence_number)] == [event.provider_event_id for event in first.events]


def test_event_participant_requires_exactly_one_canonical_reference():
    with pytest.raises(ValidationError):
        NormalizedEventParticipant(role=ParticipantRole.SHOOTER)
    with pytest.raises(ValidationError):
        NormalizedEventParticipant(role=ParticipantRole.SHOOTER, team_external_id="team-redwood", player_external_id="player-ember")
