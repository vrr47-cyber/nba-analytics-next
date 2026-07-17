# NBA Analytics Implementation Plan

Status: Phase 3A — fixture-backed provider boundary complete

## Phase 0 — specifications and decisions

Complete the product boundary, architecture, frontend decision, data contracts, coverage rules, source strategy, model plan, agent rules, and decision log. No backend or additional frontend implementation is authorized during this phase.

## Phase 1 — repository and contracts

Complete: target monorepo directories, Python project metadata, React/Vite frontend shell, typed API mirror, PostgreSQL configuration, foundation migration baseline, structured logging, provider protocols, synthetic safety tests, OpenAPI checks, and repository hygiene checks. No external data is ingested.

## Phase 2 — canonical entities and coverage

Phase 2A/2B complete locally: canonical entities, provider mappings, normalized batches, source-run lifecycle, repositories, ingestion boundaries, coverage contracts, manifest-driven JSONL validation, and synthetic fixtures. PostgreSQL execution remains pending because Docker is unavailable. No truth provider, real data, or public entity endpoints.

## Phase 3 — completed-game analytics

### Phase 3A — Teams provider boundary

Complete on `phase-3-provider-ingestion`: provider registry/factory, normalized fixture DTOs, a deterministic fictional Teams adapter, versioned active-team scope policy, source-run provenance, coverage evaluation, provider-ID identity binding, and a PostgreSQL migration for generic league-provider mappings. No network calls, credentials, real NBA data, releases, frontend changes, or publication are included.

### Phase 3B — Players and rosters

Complete on `phase-3-player-roster-ingestion`: separate player and roster services, deterministic revisioned fixture DTOs, provider-mapping-first player identity, required existing team/player mappings for rosters, stable season roster memberships, synthetic withholding, and removal of global player-slug uniqueness. No real provider, API, frontend, game, schedule, stats, or model work is included.

Ingest and validate completed-game team/player summaries. Publish Explore, Teams, Players, standings, and power data only through the publication layer. Add explicit source/date/sample context.

## Phase 4 — shot analytics

Add shot normalization, eligibility rules, shot profiles, expected-value modeling, and actual-versus-expected outputs. Keep the module withheld when coverage is insufficient.

## Phase 5 — forecasts and models

Add power rating, pre-game probability, playoff simulation, model registry, evaluation, calibration, and shadow inference. Publish only versioned, qualified outputs.

## Phase 6 — transient Live

Add the live provider adapter, Redis expiry, live feature builder, win-probability API, compact summary retention, and live freshness status. Do not create a complete play-by-play archive.

## Phase 7 — hardening

Add monitoring, contract tests, release checks, accessibility validation, performance budgets, security review, source-term review, and deployment runbooks.

## Definition of done for implementation work

- documentation and decision record updated;
- contract and truth tests pass;
- coverage report passes publication threshold;
- provenance is visible in API and UI;
- missing data is null/withheld, not zero-filled;
- model outputs carry version and limitations;
- no realistic placeholder NBA statistics appear outside `design-prototype`;
- production deployment is reproducible from a clean clone.
