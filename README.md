# NBA Analytics

Provider-neutral Phase 1 foundation for a stats-first NBA analytics product.
This phase intentionally does not ingest NBA data, publish metrics, train models,
or use unofficial NBA endpoints. The `design-prototype` branch is preserved
separately and is not production data.

## Stack

- FastAPI and SQLAlchemy/Alembic backend
- React with Vite and TypeScript frontend
- PostgreSQL runtime database
- Redis deferred until the Live phase
- pnpm for JavaScript workspaces

## Local setup

Prerequisites: Python 3.12+, Node.js 22+, pnpm 11+, and PostgreSQL (or Docker).

```bash
cp .env.example .env
python -m pip install -e 'backend[dev]'
pnpm install
docker compose -f infra/docker/docker-compose.yml up -d postgres
pnpm run db:migrate
pnpm run backend:dev
pnpm run frontend:dev
```

`/health/live` checks only process availability. `/health/ready` reports database
and provider readiness. `/api/v1/status` and `/api/v1/meta/seasons` are truthful
when the database is clean: no validated dataset is reported as available.

## Checks

```bash
pnpm run backend:lint
pnpm run backend:typecheck
pnpm run backend:test
pnpm run frontend:lint
pnpm run frontend:test
pnpm run frontend:build
pnpm run api:openapi && pnpm run api:check
pnpm run repo:check
```

Synthetic fixtures, when explicitly enabled for tests, use invented entities and
are never publication-ready. Realistic placeholder NBA statistics are prohibited
outside the clearly labeled `design-prototype` branch.

Validate the provider-neutral synthetic bundle without database access:

```bash
python -m backend.app.jobs.import_dataset_bundle \
  --bundle backend/tests/fixtures/synthetic_bundle \
  --validate-only --allow-synthetic --json
```

Synthetic bundles are rejected by default and are forbidden in production.

Phase 2A migration validation requires PostgreSQL. Apply it with
`pnpm run db:migrate` after the database is available; Docker was unavailable in
the local implementation environment, so live migration execution remains a CI
or developer-machine check.
