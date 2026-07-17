# Current State

As of 2026-07-17

## Repository

- Git repository: `nba-analytics-next`.
- `main` contains the Phase 0 documentation and the merged Phase 1/Phase 2 foundation.
- `design-prototype` preserves the visual dashboard prototype and its synthetic-data warning.
- The repository has a local `origin` configured from the requested GitHub repository; its upstream branch is currently absent because the remote repository had no initial commit when cloned.

## Product status

Phase 1 foundation is implemented. No production analytics data pipeline or model exists. The visual prototype is not a source of truth for metrics, architecture, or production technology.

Phase 2A/2B is merged: canonical entity models, provider-ID mappings, normalized ingestion contracts, transactional writers, bundle validation/import, and coverage evaluation contracts are present.

The backend exposes process health, database/provider readiness, truthful status, and an empty seasons envelope. The frontend is a small React/Vite shell with Explore and Data Status routes. Phase 2B adds canonical repositories, ingestion boundaries, and a manifest-driven JSONL validator; no NBA data or provider adapter exists.

## Prototype status

The prototype branch contains a single Explore-style dashboard with responsive presentation, local UI interactions, and illustrative content. It is clearly labeled `DESIGN PROTOTYPE — SYNTHETIC PLACEHOLDER DATA` and is not approved for data publication.

## Decisions made

- Product owns analysis and interpretation; external providers own the complete archive.
- Persistent analytical data is separate from transient live state.
- PostgreSQL is the production runtime database.
- Redis is reserved for expiring live sessions.
- Production frontend selection: React with Vite.
- Realistic placeholder NBA statistics are prohibited outside `design-prototype`.
- Development fixtures are invented, synthetic, test-only, and never publishable.
- The default provider is unconfigured and makes no network calls.
- Phase 3A is implemented on `phase-3-provider-ingestion` as a provider-neutral, fixture-backed Teams boundary. The fixture is fictional, synthetic, deterministic, and makes no network calls.
- Teams ingestion records a source run and coverage evaluation only; no Teams dataset release is created, and all Teams-only publication remains withheld.
- A generic league-provider identity mapping was added because Phase 2 had mappings for teams, players, and games but not leagues.
- Phase 3B adds separate fixture-only player and roster ingestion services. Player identity uses provider mappings exclusively; no provider-independent canonical player key exists, so unmapped players are created rather than matched by name, slug, or biography. Roster rows are stable season/competition/team/player/snapshot memberships and update in place.
- Phase 4 adds fixture-only provider-neutral game and schedule ingestion. Game identity uses existing provider game mappings; structural season, competition, and home/away team identity is immutable after mapping. Game date is derived from UTC scheduled tipoff, and all fixture coverage remains withheld.
- Phase 5 adds fixture-only provider-neutral complete box-score ingestion. Team and player game-stat rows are validated before one atomic write, use existing provider mappings, enforce final-score and team/player point consistency, validate complete fixture roster observations, and remain withheld. No player-game uniqueness migration was added; the stronger `(game, player)` rule is enforced in the service.
- Phase 6 adds fixture-only provider-neutral completed-game play-by-play ingestion. Events use durable `(game, provider, provider_event_id)` identity, typed canonical participants, deterministic sequence ordering, complete score reconciliation against Phase 4/5, atomic correction handling, and withheld synthetic coverage. No live ingestion, API, frontend, model, or release capability exists.
- Phase 7 adds the first product vertical slice on `phase-7-team-analytics`: publication-aware team directory and detail APIs, shared aggregate metric definitions, trends, roster summaries, bounded recent games, and React/Vite Teams routes. The slice is query-based with no migration or derived-metric table. Synthetic recorded samples remain visible only in development/test with `publishable=false`; no conference rank, shot profile, power model, live module, or player detail route is included.
- Phase 8 adds the provider-neutral Player Analytics vertical slice on `phase-8-player-analytics`: bounded publication-aware player directory/detail APIs, DNP-safe metrics, per-game and per-36 values, trends, recent logs, narrow splits, explicit current-team versus statistical-team attribution, and React/Vite Players routes. No migration, transaction-history model, player comparison, shot analytics, ranking, or unsupported biography data is included. Synthetic samples remain withheld.
- Phase 9 adds the compact Explore dashboard on `phase-9-explore-dashboard`. It composes the existing Team and Player Analytics services, adds only a bounded `/api/v1/explore` composition endpoint for featured sections and global recent final games, and keeps the root `/` route as the single product landing page. No new metrics, rankings, caching, Redis, live data, or migration was added. Synthetic recorded samples remain visibly withheld.

## Not yet decided or approved

- Primary and validation provider contracts for real data.
- Field-level source mappings and licensing review.
- Exact coverage tolerances and qualification thresholds.
- PostgreSQL hosting and object-storage provider.
- Redis hosting and live retention duration.
- Authentication and access policy.
- Production domains and deployment environment.
- Model features, training data, and evaluation thresholds.
- PostgreSQL execution of the Phase 2A/2B migrations and repository integration is configured in GitHub Actions; local execution is pending because Docker and the PostgreSQL client are unavailable.
