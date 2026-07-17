# Team analytics methodology

Phase 7 team analytics is query-derived from canonical final-game scores and team box scores. No derived-metric table or migration is used.

## Metric version

The metric registry version is `team-analytics.v1`.

Estimated possessions are calculated consistently as:

```text
FGA + 0.44 × FTA − ORB + TOV
```

For a team scope, ratings use aggregated totals rather than averages of game-level ratings:

```text
ORtg = 100 × total points / total estimated possessions
DRtg = 100 × total opponent points / total opponent estimated possessions
Net Rating = ORtg − DRtg
```

The initial pace implementation uses the average of the team and opponent estimated possessions, normalized to 48 minutes. Canonical game duration is not yet available for safe overtime handling, so pace is an estimated regulation-normalized value and is marked estimated in metadata.

Shooting and possession ratios are calculated from aggregate numerators and denominators:

```text
eFG% = (total FGM + 0.5 × total 3PM) / total FGA
TS% = total points / (2 × (total FGA + 0.44 × total FTA))
TOV% = total TOV / (total FGA + 0.44 × total FTA + total TOV)
ORB% = total ORB / (total ORB + opponent total DRB)
FTr = total FTA / total FGA
```

Zero or unavailable denominators produce `null`, never zero. The API exposes unavailable values as `null`; the frontend renders them as an em dash.

## Scope and eligibility

Only final games with both participant team-stat rows are eligible. Season and competition filters are applied to canonical foreign keys. Records are ordered by scheduled start and canonical game ID as a deterministic tie-breaker.

Last 10 means the most recent ten eligible games. If fewer than ten games exist, the response includes the available sample size and does not label it as a complete last-10 or full-season result.

Roster output uses the latest valid `RosterSnapshot` on or before the requested scope end date. This is an observed snapshot, not transaction history or proof of continuous membership.

Conference rank is intentionally omitted because the fixture warehouse does not provide a verified standings basis for that value.

## Publication and provenance

Team endpoints use the shared data, scope, coverage, provenance, and publication envelope. Synthetic development data may be returned as a recorded sample, but always has `synthetic=true`, `publishable=false`, and the reason `Synthetic recorded sample — not publishable.` No dataset release is created.

Multi-run aggregates expose the contributing source-run count and the latest available source update rather than falsely claiming a single source observation.
