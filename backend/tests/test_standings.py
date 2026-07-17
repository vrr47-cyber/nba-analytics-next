from uuid import uuid4

from backend.app.schemas.standings import StandingRow
from backend.app.schemas.teams import TeamMetrics
from backend.app.services.standings import _power_sort_key, _standings_sort_key


def _row(name: str, *, wins: int, losses: int, differential: int, net: float | None) -> StandingRow:
    games = wins + losses
    return StandingRow(team_id=uuid4(), team_name=name, abbreviation=name[:3].upper(), games_played=games, wins=wins, losses=losses, win_percentage=wins / games if games else None, points_for=100, points_against=100 - differential, point_differential=differential, metrics=TeamMetrics(net_rating=net), power_value=net)


def test_recorded_standings_order_is_deterministic():
    rows = [_row("Alpha", wins=2, losses=0, differential=4, net=1), _row("Bravo", wins=1, losses=1, differential=20, net=8), _row("Charlie", wins=2, losses=0, differential=4, net=None)]
    ordered = sorted(rows, key=_standings_sort_key)
    assert [row.team_name for row in ordered] == ["Alpha", "Charlie", "Bravo"]


def test_power_order_uses_net_rating_then_recorded_tiebreakers():
    rows = [_row("Alpha", wins=2, losses=0, differential=4, net=1), _row("Bravo", wins=1, losses=1, differential=20, net=8), _row("Charlie", wins=2, losses=0, differential=4, net=None)]
    ordered = sorted(rows, key=_power_sort_key)
    assert [row.team_name for row in ordered] == ["Bravo", "Alpha", "Charlie"]
