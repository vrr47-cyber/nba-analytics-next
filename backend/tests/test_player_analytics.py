from datetime import datetime, timezone
from uuid import uuid4

import pytest

from backend.app.database.models import Game, Player, PlayerGameStats, Team
from backend.app.services.player_analytics import PlayerAnalyticsError, _PlayerAggregate, _PlayerRow


def _row(participation: str = "played", team_id=None, points: int = 20, fga: int = 10, fgm: int = 5, minutes: str | None = "30:00") -> _PlayerRow:
    team_id = team_id or uuid4()
    opponent_id = uuid4()
    game = Game(id=uuid4(), season_id=uuid4(), competition_id=uuid4(), scheduled_start=datetime(2099, 1, 1, tzinfo=timezone.utc), game_date=datetime(2099, 1, 1).date(), home_team_id=team_id, away_team_id=opponent_id, status="final", home_final_score=100, away_final_score=90, neutral_site=False, source_run_id=uuid4())
    team = Team(id=team_id, league_id=uuid4(), slug="fixture", full_name="Fixture Team", short_name="Fixture", abbreviation="FIX")
    player = Player(id=uuid4(), slug="fixture-player", full_name="Fixture Player", position="SG", active=True)
    stats = PlayerGameStats(id=uuid4(), game_id=game.id, player_id=player.id, team_id=team_id, starter=True, participation_status=participation, minutes=minutes, points=points if participation == "played" else 0, field_goals_made=fgm if participation == "played" else 0, field_goals_attempted=fga if participation == "played" else 0, three_pointers_made=2 if participation == "played" else 0, three_pointers_attempted=4 if participation == "played" else 0, free_throws_made=8 if participation == "played" else 0, free_throws_attempted=10 if participation == "played" else 0, offensive_rebounds=1 if participation == "played" else 0, defensive_rebounds=3 if participation == "played" else 0, total_rebounds=4 if participation == "played" else 0, assists=5 if participation == "played" else 0, steals=1 if participation == "played" else 0, blocks=1 if participation == "played" else 0, turnovers=2 if participation == "played" else 0, personal_fouls=2 if participation == "played" else 0, source_run_id=uuid4())
    return _PlayerRow(stats, game, team)


def test_games_available_excludes_dnp_from_played_metrics() -> None:
    first = _row("played", points=20)
    second = _row("did_not_play", team_id=first.team.id, minutes=None)
    player = Player(id=first.stats.player_id, slug="fixture", full_name="Fixture Player", position="SG", active=True)
    aggregate = _PlayerAggregate(player, [first, second], first.team.id, first.team.full_name, "single_team", {first.team.id: first.team.full_name})
    metrics = aggregate.metrics()
    assert metrics.games_available == 2
    assert metrics.games_played == 1
    assert metrics.non_participation_count == 1
    assert metrics.points_per_game == 20


def test_aggregate_percentages_are_not_averaged() -> None:
    first = _row("played", points=20, fga=10, fgm=5)
    second = _row("played", team_id=first.team.id, points=20, fga=20, fgm=2)
    player = Player(id=first.stats.player_id, slug="fixture", full_name="Fixture Player", position="SG", active=True)
    aggregate = _PlayerAggregate(player, [first, second], first.team.id, first.team.full_name, "single_team", {first.team.id: first.team.full_name})
    metrics = aggregate.metrics()
    assert metrics.field_goal_percentage == 7 / 30
    assert metrics.field_goal_percentage != ((5 / 10) + (2 / 20)) / 2
    assert metrics.points_per_36 == 24


def test_played_zero_minutes_is_invalid() -> None:
    row = _row("played", minutes="00:00")
    player = Player(id=row.stats.player_id, slug="fixture", full_name="Fixture Player", position="SG", active=True)
    aggregate = _PlayerAggregate(player, [row], row.team.id, row.team.full_name, "single_team", {row.team.id: row.team.full_name})
    with pytest.raises(PlayerAnalyticsError, match="positive minutes"):
        aggregate.metrics()


def test_multi_team_attribution_is_explicit() -> None:
    first = _row("played")
    second = _row("played", team_id=uuid4())
    player = Player(id=first.stats.player_id, slug="fixture", full_name="Fixture Player", position="SG", active=True)
    second.stats.player_id = player.id
    aggregate = _PlayerAggregate(player, [first, second], None, None, "multiple_teams", {first.team.id: first.team.full_name, second.team.id: second.team.full_name})
    attribution = aggregate.attribution()
    assert attribution.state == "multiple_teams"
    assert len(attribution.team_ids) == 2
