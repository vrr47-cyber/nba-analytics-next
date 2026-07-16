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
