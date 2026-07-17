from datetime import datetime, timezone
from uuid import uuid4

from backend.app.database.models import Game, Team, TeamGameStats
from backend.app.domain.metrics import estimated_possessions, ratio
from backend.app.schemas.envelope import Provenance, Scope
from backend.app.schemas.teams import TeamListResponse
from backend.app.services.team_analytics import _Aggregate, coverage_for


def _game(home: bool = True) -> tuple[Game, TeamGameStats, TeamGameStats]:
    home_id, away_id = uuid4(), uuid4()
    game = Game(
        id=uuid4(), season_id=uuid4(), competition_id=uuid4(), scheduled_start=datetime(2099, 1, 1, tzinfo=timezone.utc),
        game_date=datetime(2099, 1, 1).date(), home_team_id=home_id, away_team_id=away_id, status="final",
        home_final_score=100, away_final_score=90, neutral_site=False, source_run_id=uuid4(),
    )
    team = TeamGameStats(
        id=uuid4(), game_id=game.id, team_id=home_id if home else away_id, opponent_team_id=away_id if home else home_id,
        home_away="home" if home else "away", result="W" if home else "L", minutes="48:00", points=100 if home else 90,
        field_goals_made=40, field_goals_attempted=80, three_pointers_made=10, three_pointers_attempted=30,
        free_throws_made=10, free_throws_attempted=12, offensive_rebounds=10, defensive_rebounds=30, total_rebounds=40,
        assists=20, steals=5, blocks=3, turnovers=10, personal_fouls=15, source_run_id=uuid4(),
    )
    opponent = TeamGameStats(
        id=uuid4(), game_id=game.id, team_id=away_id if home else home_id, opponent_team_id=home_id if home else away_id,
        home_away="away" if home else "home", result="L" if home else "W", minutes="48:00", points=90 if home else 100,
        field_goals_made=36, field_goals_attempted=80, three_pointers_made=8, three_pointers_attempted=28,
        free_throws_made=10, free_throws_attempted=12, offensive_rebounds=8, defensive_rebounds=28, total_rebounds=36,
        assists=18, steals=4, blocks=2, turnovers=12, personal_fouls=16, source_run_id=uuid4(),
    )
    return game, team, opponent


def test_possessions_and_ratios_use_aggregate_denominators() -> None:
    assert estimated_possessions(80, 12, 10, 10) == 85.28
    assert ratio(100, 0) is None
    first_game = _game()
    second_game = _game()
    second_game[1].field_goals_attempted = 100
    second_game[1].field_goals_made = 20
    first = first_game[1]
    second = second_game[1]
    aggregate = _Aggregate([first_game, second_game])
    metrics = aggregate.metrics()
    expected_efg = (first.field_goals_made + second.field_goals_made + 0.5 * (first.three_pointers_made + second.three_pointers_made)) / (first.field_goals_attempted + second.field_goals_attempted)
    assert metrics.effective_fg_percentage == expected_efg
    assert metrics.effective_fg_percentage != (0.5 * ((first.field_goals_made + 0.5 * first.three_pointers_made) / first.field_goals_attempted) + 0.5 * ((second.field_goals_made + 0.5 * second.three_pointers_made) / second.field_goals_attempted))
    assert metrics.games_played == 2
    assert second.field_goals_attempted != 0


def test_coverage_keeps_synthetic_sample_withheld() -> None:
    team_id = uuid4()
    team = Team(id=team_id, league_id=uuid4(), slug="fixture", full_name="Fixture Team", short_name="Fixture", abbreviation="FIX")
    coverage, publication, provenance = coverage_for(team, _Aggregate([]), synthetic=True)
    assert coverage.is_publishable is False
    assert publication.publishable is False
    assert provenance.synthetic is True


def test_shared_envelope_carries_scope_and_publication() -> None:
    response = TeamListResponse(
        data=[], scope=Scope(season="2099-00", competition="regular"), coverage={"reason": "empty"},
        provenance=Provenance(synthetic=True), publication={"publishable": False, "code": "synthetic_fixture", "reason": "fixture"},
    )
    assert response.scope.season == "2099-00"
    assert response.publication.publishable is False
