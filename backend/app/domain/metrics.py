from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricDefinition:
    id: str
    label: str
    formula: str
    unit: str
    version: str
    direction: str
    estimated: bool
    null_behavior: str
    qualification: str = "Requires valid canonical source fields."


METRIC_VERSION = "team-analytics.v1"

METRICS = {
    "offensive_rating": MetricDefinition("offensive_rating", "ORtg", "100 * points / possessions", "rating", METRIC_VERSION, "higher_is_better", True, "null when possessions are zero or unavailable"),
    "defensive_rating": MetricDefinition("defensive_rating", "DRtg", "100 * opponent points / opponent possessions", "rating", METRIC_VERSION, "lower_is_better", True, "null when opponent possessions are zero or unavailable"),
    "net_rating": MetricDefinition("net_rating", "Net Rating", "ORtg - DRtg", "rating", METRIC_VERSION, "higher_is_better", True, "null when either rating is unavailable"),
    "pace": MetricDefinition("pace", "Pace", "48 * average game possessions / actual minutes", "possessions per 48", METRIC_VERSION, "higher_is_better", True, "null when duration is unavailable"),
    "effective_fg_percentage": MetricDefinition("effective_fg_percentage", "eFG%", "(FGM + 0.5 * 3PM) / FGA", "ratio", METRIC_VERSION, "higher_is_better", False, "null when FGA is zero or unavailable"),
    "true_shooting_percentage": MetricDefinition("true_shooting_percentage", "TS%", "PTS / (2 * (FGA + 0.44 * FTA))", "ratio", METRIC_VERSION, "higher_is_better", True, "null when shooting denominator is zero or unavailable"),
    "turnover_percentage": MetricDefinition("turnover_percentage", "TOV%", "TOV / (FGA + 0.44 * FTA + TOV)", "ratio", METRIC_VERSION, "lower_is_better", True, "null when denominator is zero or unavailable"),
    "offensive_rebound_percentage": MetricDefinition("offensive_rebound_percentage", "ORB%", "ORB / (ORB + opponent DRB)", "ratio", METRIC_VERSION, "higher_is_better", False, "null when rebound denominator is zero or unavailable"),
    "free_throw_rate": MetricDefinition("free_throw_rate", "FTr", "FTA / FGA", "ratio", METRIC_VERSION, "higher_is_better", False, "null when FGA is zero or unavailable"),
}

PLAYER_METRICS = {
    "field_goal_percentage": MetricDefinition("field_goal_percentage", "FG%", "sum FGM / sum FGA", "ratio", "player-analytics.v1", "higher_is_better", False, "null when FGA is zero or unavailable"),
    "three_point_percentage": MetricDefinition("three_point_percentage", "3P%", "sum 3PM / sum 3PA", "ratio", "player-analytics.v1", "higher_is_better", False, "null when 3PA is zero or unavailable"),
    "free_throw_percentage": MetricDefinition("free_throw_percentage", "FT%", "sum FTM / sum FTA", "ratio", "player-analytics.v1", "higher_is_better", False, "null when FTA is zero or unavailable"),
    "player_effective_fg_percentage": MetricDefinition("player_effective_fg_percentage", "eFG%", "(sum FGM + 0.5 * sum 3PM) / sum FGA", "ratio", "player-analytics.v1", "higher_is_better", False, "null when FGA is zero or unavailable"),
    "player_true_shooting_percentage": MetricDefinition("player_true_shooting_percentage", "TS%", "sum PTS / (2 * (sum FGA + 0.44 * sum FTA))", "ratio", "player-analytics.v1", "higher_is_better", True, "null when shooting denominator is zero or unavailable"),
    "three_point_attempt_rate": MetricDefinition("three_point_attempt_rate", "3PA Rate", "sum 3PA / sum FGA", "ratio", "player-analytics.v1", "higher_is_better", False, "null when FGA is zero or unavailable"),
    "player_free_throw_rate": MetricDefinition("player_free_throw_rate", "FTr", "sum FTA / sum FGA", "ratio", "player-analytics.v1", "higher_is_better", False, "null when FGA is zero or unavailable"),
}


def estimated_possessions(field_goals_attempted: int, free_throws_attempted: int, offensive_rebounds: int, turnovers: int) -> float:
    return field_goals_attempted + 0.44 * free_throws_attempted - offensive_rebounds + turnovers


def ratio(numerator: float, denominator: float) -> float | None:
    return None if denominator <= 0 else numerator / denominator
