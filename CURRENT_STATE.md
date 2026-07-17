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
