# Agent Rules for NBA Analytics

## Scope

This repository is a greenfield NBA analytics project. Do not reference, copy, or infer architecture from any previous NBA Analytics repository unless the user explicitly instructs you to do so.

## Phase gate

The project is paused at Phase 0 until the product, data, coverage, source, and model specifications are approved. Do not implement the backend or add frontend features while Phase 0 is paused.

## Data safety

- Accuracy before polish.
- Never present a partial sample as a complete season.
- Never rank an invalid or incomplete comparison population.
- Never convert missing values to zero.
- Every published number must include provenance and context.
- Model probabilities are estimates, never guarantees.
- The frontend must not calculate authoritative basketball metrics.

## Placeholder policy

Realistic placeholder NBA statistics are prohibited outside the clearly labeled `design-prototype` branch. The prototype must keep the prominent label `DESIGN PROTOTYPE — SYNTHETIC PLACEHOLDER DATA`. Any example values in docs or tests must be clearly synthetic and must not be presented as current, live, official, predicted, or model-generated.

## Architecture boundaries

Persistent analytical data and transient live data are separate systems. PostgreSQL is the production runtime database. Redis is for expiring live sessions only. Raw and training artifacts are stored outside Git. FastAPI publishes approved responses; source adapters do not live in route handlers.

## Frontend decision

Production frontend is React with Vite, TypeScript, and explicit routing. The prototype stack is not binding. Keep API separation explicit and do not add server-rendering complexity without an approved decision record.

## Change discipline

Before implementation, read the relevant specification and decision log. Keep changes scoped. Run documentation consistency checks, contract tests, and build checks appropriate to the change. Do not commit credentials, raw provider data, model binaries, or local database files.
