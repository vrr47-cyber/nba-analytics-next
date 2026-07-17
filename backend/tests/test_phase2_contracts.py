from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from backend.app.domain.canonical import BoxScoreLine, NormalizedGame, validate_season_code
from backend.app.domain.coverage_contracts import CoverageEvaluationInput, CompletenessState, evaluate_coverage
from backend.app.domain.publication import PublicationCode, PublicationDecision


def test_season_format_is_shared_and_strict():
    assert validate_season_code("2099-00") == "2099-00"
    with pytest.raises(ValueError):
        validate_season_code("2099")
    with pytest.raises(ValueError):
        validate_season_code("2099-02")


def test_final_game_requires_scores_and_distinct_participants():
    base = {"provider": "synthetic", "external_id": "fixture-game", "retrieved_at": datetime.now(timezone.utc).isoformat()}
    with pytest.raises(ValidationError):
        NormalizedGame(source=base, season="2099-00", competition_code="regular", scheduled_start="2099-01-01T00:00:00Z", game_date="2099-01-01", home_team_external_id="red", away_team_external_id="blue", status="final")
    with pytest.raises(ValidationError):
        NormalizedGame(source=base, season="2099-00", competition_code="regular", scheduled_start="2099-01-01T00:00:00Z", game_date="2099-01-01", home_team_external_id="red", away_team_external_id="red", status="scheduled")


def test_box_score_rejects_negative_and_made_over_attempts():
    fields = dict(points=1, field_goals_made=2, field_goals_attempted=1, three_pointers_made=0, three_pointers_attempted=0, free_throws_made=0, free_throws_attempted=0, offensive_rebounds=0, defensive_rebounds=0, total_rebounds=0, assists=0, steals=0, blocks=0, turnovers=0, personal_fouls=0)
    with pytest.raises(ValidationError):
        BoxScoreLine(**fields)
    fields["field_goals_made"] = 0
    fields["points"] = -1
    with pytest.raises(ValidationError):
        BoxScoreLine(**fields)


def test_coverage_unknown_denominator_is_not_publishable():
    result = evaluate_coverage(CoverageEvaluationInput(dataset_name="fixture", observed_count=3))
    assert result.completeness == CompletenessState.UNKNOWN
    assert result.ratio is None
    assert result.publishable is False


def test_synthetic_publication_is_blocked_even_when_complete():
    decision = PublicationDecision.from_coverage("complete", synthetic=True)
    assert decision.code == PublicationCode.SYNTHETIC_FIXTURE
    assert decision.publishable is False
