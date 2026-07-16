# NBA Analytics Data Contracts

Status: Phase 0 — contract definition

## Contract rules

- Every persisted entity has a stable provider-independent ID and provider source ID.
- Every analytical record carries season, competition, source, source retrieval time, effective date, and schema version.
- Numeric values use explicit units and precision.
- Null means unavailable or not applicable; zero means measured zero.
- The frontend receives typed publication-ready responses, never raw provider payloads.
- A response must include enough context for a user to understand what the value means.

## Core entities

### Team

Required fields: `team_id`, `provider_team_id`, `name`, `abbreviation`, `conference`, `division`, `active_from`, `active_to`, `source_id`, `source_retrieved_at`, `schema_version`.

### Player

Required fields: `player_id`, `provider_player_id`, `name`, `position` when supported, `birth_date` when supported, `active_from`, `active_to`, source metadata, and schema version.

### Roster membership

Required fields: `season_id`, `competition_id`, `team_id`, `player_id`, `start_date`, `end_date` when known, role only when sourced, and provenance. A roster record must not be used as on-court lineup data.

### Completed game summary

Required fields: `game_id`, `provider_game_id`, `season_id`, `competition_id`, `game_date`, home and away team IDs, final score, completion status, source metadata, and ingestion batch ID. Full provider play-by-play is not a required persistent entity.

### Team and player box-score summary

Required fields: game ID, entity ID, minutes, supported counting statistics, source metadata, coverage batch, and validation status. Derived metrics must reference the formula version that produced them.

### Shot attempt

Required fields: `shot_id`, game ID, player ID, team ID, shot location representation, result, shot context when supported, source metadata, and coverage status. Expected FG% and expected points are derived fields and cannot be treated as source facts.

### Metric observation

Required fields: entity ID, metric key, value, unit, season, competition, date range, sample size, qualification rule ID, population ID, calculation version, source snapshot IDs, coverage status, publication status, and generated timestamp.

### Model prediction

Required fields: prediction ID, target entity or game ID, model registry key, model version, generated timestamp, feature snapshot ID, training data cutoff, calibration metadata, input coverage summary, value, uncertainty or calibration interval when available, limitations, and publication status.

### Coverage record

Required fields: domain, scope, expected count, observed count, completeness ratio, freshness timestamp, status, reason, source snapshot IDs, and release decision.

## API response envelope

All publication endpoints use an envelope with:

```json
{
  "data": {},
  "context": {
    "season": "2025-26",
    "competition": "regular_season",
    "date_range": {"start": "YYYY-MM-DD", "end": "YYYY-MM-DD"},
    "sample_size": 0,
    "coverage_status": "complete",
    "source_ids": [],
    "calculation_version": "metrics.v1"
  },
  "publication": {
    "status": "published",
    "generated_at": "ISO-8601",
    "qualification_rule": "rule-id",
    "limitations": []
  }
}
```

`publication.status` is one of `published`, `withheld`, `partial_labeled`, or `experimental`. `withheld` responses explain why a metric is unavailable; they do not substitute zeroes.

## Live response

The live endpoint may return current score, clock, period, normalized state, prediction, probability points, source update time, model version, and cache expiry. It must not expose raw provider payloads or imply that a probability is a guarantee.

## Versioning

Breaking changes require a new contract version and compatibility window. Source schema changes, metric formula changes, qualification changes, and model changes are independently versioned and recorded in provenance.
# Phase 2A canonical data contracts

Canonical identifiers are internal UUIDs. Provider identifiers are stored in
separate provider mapping tables and never become canonical keys. Seasons use
one shared `YYYY-YY` validator; competitions are structural metadata and are
recognized as `regular`, `playoffs`, `preseason`, or `summer_league` without
implying that validated data exists for each category.

Persistent entities are leagues, seasons, competitions, teams, players, roster
snapshots, games, team/player final-game statistics, standings snapshots, and
coverage evaluations. Games deliberately contain schedule and final-result
state only: live score, period, clock, possession, and play-by-play are absent.
Roster snapshots preserve observations; absence does not invent a departure or
transaction date. Standings are timestamped snapshots, never overwritten.

Normalized provider records are in `backend/app/domain/canonical.py` and use
provider-neutral names plus source metadata. Missing optional fields remain
null. DNP is represented by `participation_status`, not by a played row with
zero minutes. Shot and live-state records are intentionally absent in Phase 2A.

Ingestion batches include provider, operation, retrieval/source timestamps,
schema fingerprint, request scope, normalized records, warnings, completeness
metadata, and an explicit outcome. Empty successful responses require explicit
completeness handling and are not automatically treated as successful datasets.
