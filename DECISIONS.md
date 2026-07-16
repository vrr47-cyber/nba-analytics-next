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
