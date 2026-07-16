# Current State

As of 2026-07-16

## Repository

- Git repository: `nba-analytics-next`.
- `main` contains the initial site starter and the Phase 0 documentation commit.
- `design-prototype` preserves the visual dashboard prototype and its synthetic-data warning.
- The repository has a local `origin` configured from the requested GitHub repository; its upstream branch is currently absent because the remote repository had no initial commit when cloned.

## Product status

Development is paused at Phase 0. No production backend exists. No production analytics data pipeline exists. No production model exists. The visual prototype is not a source of truth for metrics, architecture, or production technology.

## Prototype status

The prototype branch contains a single Explore-style dashboard with responsive presentation, local UI interactions, and illustrative content. It is clearly labeled `DESIGN PROTOTYPE — SYNTHETIC PLACEHOLDER DATA` and is not approved for data publication.

## Decisions made

- Product owns analysis and interpretation; external providers own the complete archive.
- Persistent analytical data is separate from transient live state.
- PostgreSQL is the production runtime database.
- Redis is reserved for expiring live sessions.
- Production frontend selection: React with Vite.
- Realistic placeholder NBA statistics are prohibited outside `design-prototype`.

## Not yet decided or approved

- Primary and validation provider contracts.
- Field-level source mappings and licensing review.
- Exact coverage tolerances and qualification thresholds.
- PostgreSQL hosting and object-storage provider.
- Redis hosting and live retention duration.
- Authentication and access policy.
- Production domains and deployment environment.
- Model features, training data, and evaluation thresholds.
