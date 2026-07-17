# Player analytics methodology

Phase 8 player analytics is query-derived from canonical final-game player statistics. It uses metric version `player-analytics.v1` and does not add a derived-metric table or migration.

## Participation and games

`games_available` is the number of final games in the selected season, competition, and team scope for which the player has any canonical `PlayerGameStats` observation, including DNP and inactive observations.

`games_played` counts only valid rows with `participation_status=played`. DNP, inactive, not-with-team, and unknown rows do not contribute to metric denominators, but remain available in bounded recent-game logs.

`games_started` is returned only when every eligible played row has a populated starter value. It is otherwise unavailable, not zero-filled. Starts are never inferred from minutes, position, or roster data.

Played rows require positive canonical minutes. Missing, malformed, or zero minutes on a played row block the affected calculation rather than becoming a zero-stat appearance.

## Aggregate metrics

Multi-game metrics use aggregate numerators and denominators:

```text
FG%  = sum FGM / sum FGA
3P%  = sum 3PM / sum 3PA
FT%  = sum FTM / sum FTA
eFG% = (sum FGM + 0.5 × sum 3PM) / sum FGA
TS%  = sum PTS / (2 × (sum FGA + 0.44 × sum FTA))
3PA rate = sum 3PA / sum FGA
FTr = sum FTA / sum FGA
```

Per-game values are aggregate totals divided by eligible games played. Per-36 values are aggregate totals divided by aggregate minutes and multiplied by 36. Zero or unavailable denominators return `null`. No minimum qualification threshold is invented; the response exposes the recorded sample and minutes.

## Team attribution

Current team is derived only from the latest valid `RosterSnapshot` on or before the selected scope end date. It may be unavailable and is never inferred from the latest game.

Statistical team attribution is derived from the canonical player-game rows in the requested scope. A team filter restricts the aggregation to that canonical team. Without a filter, one contributing team is reported as `single_team`; more than one is reported as `multiple_teams` with all contributing canonical team IDs and names. Transaction order and transaction dates are not inferred.

Duplicate player appearances for the same canonical game are rejected rather than silently summed.

## Trends and splits

Trends use chronological played rows and a five-played-game rolling window. Rolling points per game and TS% use aggregate rolling totals. DNP rows do not advance the window. Fewer than five games expose the actual sample size.

Supported splits are home, away, wins, losses, last 5, last 10, and full recorded sample. Split metrics use aggregate totals within each split. Starter/bench splits are omitted unless starter completeness is proven.

## Publication and provenance

All player endpoints return the shared data, scope, coverage, provenance, and publication envelope. Synthetic fixture data may render in development and tests, but always carries `synthetic=true`, `publishable=false`, and an explicit withheld reason. No dataset release is created.

Aggregates report contributing source-run count and latest available source update rather than implying a single source observation.
