# NBA Analytics Source Strategy

Status: Phase 0 — source policy

## Source hierarchy

1. Primary provider: preferred source for canonical teams, players, schedules, standings, completed-game summaries, and supported shot data.
2. Validation provider: independent source used for identity, score, date, and selected statistic checks.
3. Live provider: source adapter dedicated to active scoreboard and live-game state.
4. External archival links: NBA.com, Basketball Reference, or equivalent sources for experiences the product intentionally does not own.

Provider selection must be documented with licensing, terms of use, rate limits, reliability, coverage, and field-level mapping.

## Ingestion policy

- Source adapters implement a common interface.
- Fetching writes immutable raw snapshots to object storage, not directly into public tables.
- Normalization maps provider IDs to canonical IDs and records all mapping decisions.
- Validation runs before warehouse publication.
- Jobs are idempotent and can be rerun by source snapshot and batch ID.
- Rate limits, retries, backoff, and failure states are explicit.
- Credentials are environment-managed and never committed.

## Persistent versus transient data

Persist analytical data necessary for reproducible metrics and models: entities, rosters, completed-game summaries, shots, features, ratings, predictions, forecasts, coverage, and source metadata.

Do not persist the full live scoreboard update stream or turn the product into a historical play-by-play archive. Retain only a compact analytical live summary when the retention policy allows it.

## Source quality checks

Checks include schema compatibility, completeness, duplicate detection, identity resolution, date/season alignment, score reconciliation, impossible-value checks, and cross-provider spot checks.

## Source failure behavior

If the primary provider fails, the system does not silently substitute an unvalidated provider. It marks the affected domain stale or blocked, displays the data-status reason, and links to an external archival source when appropriate.

## Snapshot and retention policy

Raw and training snapshots are versioned outside Git. Retain the minimum material needed to reproduce a published release and comply with provider terms. Live caches expire automatically. Compact live summaries have a separate retention setting and must never contain the entire external play-by-play response.
