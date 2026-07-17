# NBA Analytics Implementation Plan

Status: Phase 7 — Team Analytics vertical slice implemented locally

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

### Phase 4 — Games and schedules

Complete on `phase-4-game-schedule-ingestion`: provider-mapping-first canonical game ingestion, existing-team mapping resolution, explicit scheduled/postponed/cancelled/final transitions, UTC-derived game dates, deterministic fixture revisions, atomic batch validation, synthetic withholding, and no release workflow. No live state, play-by-play, box scores, models, API, frontend, or real provider work is included.

Ingest and validate completed-game team/player summaries. Publish Explore, Teams, Players, standings, and power data only through the publication layer. Add explicit source/date/sample context.

### Phase 5 — Box scores and player game statistics

Phase 5A is implemented on `phase-5-box-score-ingestion` as a fixture-backed,
provider-neutral boundary. The adapter returns a complete final-game payload;
the service resolves existing game, team, and player mappings, validates all
rows and aggregates before persistence, and writes team and player rows in one
transaction. Exact replay is unchanged. Statistical or participation
revisions require correction mode, while identity, mapping, final-game
eligibility, roster resolution, duplicate detection, and invariants cannot be
bypassed. Redis, live data, play-by-play, shots, models, APIs, frontend work,
and releases are out of scope.

### Phase 6 — Completed-game play-by-play

Phase 6 is implemented on `phase-6-play-by-play-ingestion` as a fixture-only,
provider-neutral completed-game event boundary. The `0006_play_by_play_events`
migration adds canonical event and typed participant rows. Provider event IDs
are the durable identity; sequence is ordering metadata. Complete payloads are
prevalidated against final `Game` scores and Phase 5 `TeamGameStats`, and
player participants are resolved through mappings plus the existing roster
observation policy. Exact and reordered semantic replays are unchanged.
Correction mode permits validated field, participant, sequence, insertion, and
removal corrections while retaining canonical UUIDs; removed events are hard
deleted as a complete-snapshot replacement because no supersession schema
exists. Synthetic coverage is withheld and no release is created. Live
polling, play-by-play APIs, possessions, lineups, shot coordinates, models,
and real providers remain out of scope.

## Phase 7 — Team Analytics vertical slice

Phase 7 is implemented on `phase-7-team-analytics` as the first user-facing vertical slice. The backend exposes publication-aware `/api/v1/teams` directory, detail, roster, recent-games, and trends routes using one shared aggregate metric registry. The frontend adds `/teams` and `/teams/:teamId` using the existing React Router and dark application shell. Metrics are derived from canonical final games and team box scores; no conference rank, shot profile, power model, live module, player detail page, or derived-metric table is included. Synthetic fixture samples may render in development with an unavoidable withheld-publication state and never create a release.

## Phase 8 — Player Analytics vertical slice

Phase 8 is implemented on `phase-8-player-analytics` with publication-aware `/api/v1/players` directory, detail, recent-games, trends, and splits routes plus `/players` and `/players/:playerId` frontend routes. Player metrics use aggregate numerators and denominators, separate games available from games played, exclude DNP rows from metric denominators while preserving them in logs, and expose current roster team separately from statistical team attribution. The directory is bounded at 100 results with validated filters and stable null-last ordering. No starter split is shown without completeness, no migration or transaction-history model is added, and synthetic samples remain visibly withheld.

## Phase 9 — Explore Dashboard

Phase 9 is implemented on `phase-9-explore-dashboard` as a compact composition layer at `/`. The bounded `/api/v1/explore` endpoint delegates featured teams to Team Analytics and featured players to Player Analytics, and adds only the global bounded recent-final-games composition that cannot be assembled efficiently from team-specific endpoints without client-side N+1 requests. The frontend reuses the shared coverage banner, metric formatting, loading/error/empty patterns, and existing Teams/Players routes. Explore contains no new metric formulas, rankings, AI summaries, shot analytics, projections, live modules, caching, Redis, materialized tables, or migration. Synthetic samples remain visible only with an explicit withheld-publication state.

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
