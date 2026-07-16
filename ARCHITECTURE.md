# NBA Analytics Architecture

Status: Phase 0 — architecture decision record

## Governing rule

The website owns analysis and interpretation. External providers own the complete NBA game archive.

## Two data paths

### Persistent analytical path

Raw source snapshots → canonical validation → PostgreSQL warehouse → metrics and features → model inference → publication gates → FastAPI API → React frontend.

Persistent data includes teams, players, rosters, season standings, completed-game team and player summaries, shots, features, predictions, ratings, forecast runs, coverage metadata, and source metadata.

### Transient live path

Live provider adapter → normalized current state → expiring Redis cache → live feature builder → win-probability inference → live API response → React frontend.

The live path must not silently write a second historical archive. It may retain a compact completed-game analytical summary under the retention rules in `DATA_CONTRACTS.md`.

## Production frontend decision

### Decision: React with Vite

The production frontend will use React with Vite and a real routing library. The current visual prototype stack must not be treated as the production decision. The prototype lives on `design-prototype`; production architecture is decided here before implementation resumes.

### Comparison

| Concern | Next.js | React with Vite | Decision |
| --- | --- | --- | --- |
| Routing | File-based routing is convenient, but couples route structure to framework conventions and server features. | React Router makes route ownership explicit and works naturally for an analytics application. | React + Vite |
| Deployment | Strong when SSR, server actions, edge rendering, or framework-managed APIs are needed; adds framework/runtime coupling. | Static/client deployment is simple; API remains a separately deployed FastAPI service. | React + Vite |
| API separation | Next can host API routes, which makes accidental frontend/backend coupling easy. | Separate origin and typed client make the FastAPI publication boundary explicit. | React + Vite |
| Server rendering | Useful for public SEO pages and server-owned data. Not required for authenticated dashboards or interactive charts in the initial product. | No SSR by default; can add pre-rendering later if a measured need appears. | React + Vite |
| Complexity | More framework surface, server/client boundaries, and deployment modes to understand. | Smaller frontend surface and clearer ownership, with routing/query/cache libraries chosen intentionally. | React + Vite |
| Maintainability | Good if the team wants one full-stack framework; harder to keep API ownership separate. | Clear frontend/backend boundary and independent release cadence. | React + Vite |

The decision may be revisited only through a written decision record that identifies a demonstrated SSR, SEO, or deployment requirement. It must not be changed merely because the prototype currently uses a different starter.

## Backend

Use Python, FastAPI, Pydantic, SQLAlchemy or an equivalent typed database layer, Alembic-style migrations, structured logging, and explicit domain/service layers. Route handlers expose publication-ready responses only. Source fetching does not live inside route functions.

## Database and storage

Use PostgreSQL as the production application database. Use versioned Parquet or compressed JSON snapshots in object storage for raw and training artifacts. DuckDB may be used for offline research, never as the production runtime database. Redis is reserved for expiring live sessions.

## Background work

Begin with explicit Python CLI jobs and platform/CI scheduling. Do not introduce Airflow, Celery clusters, Kafka, or microservices until operational evidence requires them.

## Monorepo target

```text
backend/app/{api,domain,services,sources,models,database,jobs,schemas}
backend/tests/{unit,integration,contracts,truth}
frontend/src/{app,pages,features,components,api}
frontend/tests
research/{notebooks,experiments,datasets,reports}
model_artifacts/manifests
infra/{docker,scripts,ci}
docs/{decisions,methodology}
```

Raw data, training data, model binaries, credentials, and local database files are not committed to Git.
