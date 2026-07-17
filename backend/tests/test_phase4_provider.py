import pytest
from pydantic import ValidationError

from backend.app.domain.canonical import GameStatus, NormalizedGame
from backend.app.providers.registry import create_teams_provider


def test_fixture_games_have_explicit_deterministic_revisions():
    provider = create_teams_provider("fixture")
    v1, schema, fingerprint_v1, revision_v1 = provider.load_games("v1")
    replay, _, replay_fingerprint, _ = provider.load_games("v1")
    v2, _, fingerprint_v2, revision_v2 = provider.load_games("v2")

    assert len(v1) == 3
    assert schema == "fixture-games.v1"
    assert revision_v1 == "v1"
    assert revision_v2 == "v2"
    assert fingerprint_v1 == replay_fingerprint
    assert fingerprint_v1 != fingerprint_v2
    assert [game.source.external_id for game in v1] == [game.source.external_id for game in v2]
    assert v1[0].status == GameStatus.SCHEDULED
    assert v1[1].status == GameStatus.POSTPONED
    assert v1[2].status == GameStatus.FINAL
    assert v2[0].status == GameStatus.FINAL
    assert v2[0].home_final_score is not None and v2[0].away_final_score is not None
    assert v1[1].scheduled_start != v2[1].scheduled_start
    assert all(game.game_date == game.scheduled_start[:10] for game in v1 + replay + v2)


def test_normalized_game_rejects_unsupported_live_status():
    with pytest.raises(ValidationError):
        NormalizedGame(source={"provider": "fixture", "external_id": "game", "retrieved_at": "2099-01-01T00:00:00+00:00"}, season="2099-00", competition_code="regular", scheduled_start="2099-01-01T00:00:00+00:00", game_date="2099-01-01", home_team_external_id="home", away_team_external_id="away", status="live")
