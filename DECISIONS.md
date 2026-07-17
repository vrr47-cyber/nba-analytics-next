# Decision Log

## D-001 — Separate persistent analytics from transient live data

Status: Accepted

The warehouse stores reproducible analytical data. The live path uses an expiring cache and may retain only a compact analytical summary after a game. This prevents the product from becoming a second NBA.com archive while preserving its unique win-probability analysis.

## D-002 — Production frontend: React with Vite

Status: Accepted for Phase 0; revisit only with evidence

React with Vite provides explicit routing, a clean frontend/FastAPI boundary, simple deployment, and lower framework complexity for the initial interactive analytics product. Next.js remains viable if a demonstrated SSR, SEO, or server-owned UI requirement emerges. The existing design prototype stack is not binding.

## D-003 — PostgreSQL over DuckDB for runtime

Status: Accepted

PostgreSQL is the production application database. DuckDB remains allowed for offline research only. The runtime needs predictable migrations, service deployment, and shared application semantics.

## D-004 — Coverage is a publication gate

Status: Accepted

The system must refuse or label outputs when source completeness, freshness, population validity, or qualification thresholds do not pass. The UI exposes coverage status rather than hiding it.

## D-005 — Placeholder data policy

Status: Accepted

Realistic placeholder NBA statistics are prohibited outside the clearly labeled `design-prototype` branch. Prototype content must not be described as current, live, official, predicted, or model-generated.

## D-006 — Current approval blockers

Status: Requires product approval

Before implementation resumes, approve primary/validation/live providers, legal/source terms, coverage tolerances, qualification thresholds, retention periods, hosting choices, authentication scope, and baseline model evaluation targets.

## D-007 — NBA data provider strategy

Status: Recommended; requires approval and commercial confirmation

The recommended architecture is Sportradar as the primary commercial persistent/live provider, SportsDataIO as an independently contracted truth-validation source, NBA.com as a link-only official archival destination subject to written deep-link confirmation, and a stale-release/Live-off fallback rather than an unlicensed scraper. BALLDONTLIE, `nba_api`, NBA.com endpoints, and Basketball Reference remain research or link-only options under their published restrictions.

The recommendation is based on technical fit, not a claim that public documentation grants all required rights. The production gate is a signed agreement that names the product, covers the needed NBA fields including shot attempts, permits the required storage and display, states attribution, and defines retention, deletion, rate, SLA, and commercial terms.

## D-008 — Do not treat endpoint access as permission

Status: Accepted

The existence of `nba_api` or an accessible NBA.com endpoint does not establish authorization to collect, store, train on, redistribute, or commercially display the data. The same rule applies to scraping Basketball Reference or using a low-cost aggregator beyond its published terms.

## D-009 — Standardize the monorepo on pnpm

Status: Accepted

The JavaScript workspace uses pnpm and one committed `pnpm-lock.yaml`. npm lockfiles and generated dependency directories are not tracked.

## D-010 — Phase 1 provider-neutral foundation

Status: Accepted

Phase 1 defines replaceable provider protocols, publication envelopes, PostgreSQL migration readiness, and a truthful no-data application shell. It does not integrate a commercial provider or create NBA domain tables.

## D-011 — OpenAPI contract policy

Status: Accepted

Policy B is used for Phase 1: OpenAPI is generated from FastAPI during checks and validated for required paths. A checked-in generated frontend client is deferred until canonical response schemas stabilize; the frontend keeps a small typed mirror for the shell.

## D-012 — Synthetic fixture isolation

Status: Accepted

Synthetic fixtures are explicitly opt-in, use invented names, carry synthetic and non-publishable markers, and are unavailable in production. No realistic NBA placeholder statistics are permitted outside `design-prototype`.

## D-013 — Canonical observations are append-preserving

Status: Accepted

Roster membership and standings are observations. New snapshots are added; absence does not invent transactions, and standings snapshots are not overwritten. Games may progress from scheduled to final, while final participant identity cannot silently regress.

## D-014 — Phase 2A does not imply publication readiness

Status: Accepted

Canonical schema readiness, a source run, or a complete-looking count does not publish a dataset. Coverage, consistency, freshness, truth validation, and synthetic-data policy remain explicit publication gates.

## D-015 — Offline bundles are provider-neutral JSONL

Status: Accepted

Future licensed exports enter through a versioned manifest and checksum-verified
JSONL bundle. Synthetic bundles require explicit test-mode permission and can
never create a publishable release.

## D-016 — Phase 3A fixture-backed Teams boundary

Status: Accepted for Phase 3A

Phase 3A implements only a deterministic fictional Teams provider behind a
registry/factory. It requires no paid provider, account, credentials, or
network call. Teams ingestion records a source run and coverage evaluation,
but does not create a dataset release; all Teams-only publication remains
withheld. The expected active-team population is owned by a versioned scope
policy, and provider mappings are authoritative for identity.

Phase 2 had no generic league-provider mapping, so Phase 3A adds that minimal
identity migration. No other Phase 3 dataset or live/model capability is
included.

## D-017 — Phase 3B player and roster identity

Status: Accepted for Phase 3B

The repository has no genuinely stable provider-independent canonical player
identifier. Provider mappings are therefore the only automatic player
identity mechanism. Unmapped players create new canonical rows; names, slugs,
teams, birth dates, and other mutable biography are never used for automatic
cross-provider matching. Player slugs remain descriptive and are indexed but
not unique.

Roster membership uses one mutable row per season, competition, team, player,
and stable snapshot timestamp. Replays update provenance and report unchanged
domain fields; changed fixture revisions update the same row. The existing
`uq_roster_snapshot_membership` constraint supplies this idempotency because
Phase 3B requires a non-null competition and stable snapshot timestamp.

## D-018 — Phase 4 canonical game identity and lifecycle

Status: Accepted for Phase 4

The existing provider game mapping is authoritative. Once mapped, canonical
season, competition, home team, and away team are immutable during normal or
correction ingestion. Tipoff, UTC-derived game date, status, scores, neutral
site, URLs, and source timestamps are mutable only under the game lifecycle
rules. The existing `(provider_name, external_id)` game mapping uniqueness is
the identity constraint; matchup/date uniqueness is intentionally not added.

The supported lifecycle is scheduled, postponed, cancelled, and final. Final
score corrections require correction mode. Final-to-non-final correction, when
explicitly requested, clears both scores atomically. Fixture game runs create
source runs and withheld coverage evaluations but never dataset releases.

## D-019 — Phase 5 box-score identity and persistence

Status: Accepted for Phase 5A

Existing game, team, and player provider mappings remain authoritative. A
provider game mapping identifies the canonical game; each stat row resolves a
provider team or player mapping and cannot change canonical identity or team
attribution, including in correction mode. The existing database constraint
`(game_id, player_id, team_id)` is retained because repository-wide evidence
does not yet justify a migration. The Phase 5 service enforces the stronger
one-row-per-`(game_id, player_id)` invariant and rejects conflicting team rows
before persistence.

The complete fixture payload represents one final game with exactly two
participant team rows and player rows belonging only to those teams. Team
points must match the canonical final score, and player points must sum to the
team points. DNP rows have null minutes and plus/minus and zero counting stats;
played rows require a valid positive canonical minutes string. Rebound totals
must balance offensive plus defensive rebounds; no broader speculative
accounting checks are introduced.

When complete roster coverage is declared, membership is checked against the
latest `RosterSnapshot` for the same season, competition, and team whose
`snapshot_at` is on or before the UTC-derived game date. The schema has no
effective intervals, so this is an observation-based limitation, not inferred
transaction history. Fixture source runs and coverage evaluations are always
withheld and no dataset release is created.

The first fixture revision is valid and synthetic; exact replay is unchanged.
Revision v2 changes statistics and participation with stable identities and
requires correction mode. Correction mode never bypasses payload validation,
mapping resolution, final-game eligibility, roster validation, duplicate
detection, or statistical invariants.

## D-020 — Phase 6 canonical play-by-play events

Status: Accepted for Phase 6

Phase 6 adds `play_by_play_events` and typed
`play_by_play_event_participants` tables. Event identity is strictly
`(game_id, provider_name, provider_event_id)`; provider event IDs are required
and immutable. Provider sequence is ordering metadata with its own scoped
uniqueness constraint and is never used as identity. Canonical event UUIDs are
retained across replay and correction.

Participant roles are an explicit vocabulary, not arbitrary strings. Each
participant row references exactly one canonical team or player. Player
participants resolve through `PlayerProviderId` and use the existing latest
roster observation on or before the UTC-derived game date to establish team
attribution. Names, jerseys, descriptions, scores, and event position are not
identity mechanisms.

The supported event vocabulary is game start, period start, made or missed
field goal, free throw, rebound, turnover, foul, substitution, timeout, jump
ball, period end, and game end. Review and generic administrative events are
deferred. Complete fixture payloads require deterministic sequences, explicit
period boundaries, valid clocks, complete scoring progression, final-score
agreement with `Game`, and team-score agreement with Phase 5 box scores.

Normal ingestion permits only first insertion and exact semantic replay,
including reordered input. Additions, removals, sequence changes, participant
changes, and field changes require correction mode. Correction mode cannot
bypass identity, mapping, final-game eligibility, role, roster, ordering,
duplicate, clock, or score validation. Retained provider events preserve their
canonical UUIDs. Removed events and participants are hard-deleted inside the
atomic complete-snapshot correction transaction because the repository has no
supersession model. Synthetic source runs and coverage evaluations remain
withheld and no dataset release is created.

## D-021 — Phase 7 team analytics vertical slice

Status: Accepted for Phase 7

The first user-facing analytics milestone is a Team Analytics vertical slice rather than another ingestion-only phase. Team directory and detail responses are query-derived from canonical final games and team box scores, use the shared publication envelope, and reuse one versioned aggregate metric registry (`team-analytics.v1`). Multi-game ratios and ratings use aggregated numerators and denominators; per-game percentages and ratings are never averaged.

Estimated possessions use `FGA + 0.44 × FTA − ORB + TOV`. Pace is a regulation-normalized estimate because canonical duration is not yet safe for overtime handling. Conference rank is not inferred from the fixture subset. No shot profile, power rating, forecast, live module, or player-detail route is part of this slice.

Synthetic development responses may return recorded samples for truthful UI testing, but they always carry `synthetic=true`, `publishable=false`, and an explicit withheld reason. No release is created. No database migration or derived-metric table is added; query/service computation is sufficient for this milestone.
