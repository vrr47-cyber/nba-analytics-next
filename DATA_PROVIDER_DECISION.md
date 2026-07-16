# NBA Analytics Data Provider Decision

Status: Phase 0 — recommendation pending approval
Decision date: 2026-07-16

## Executive recommendation

Use a licensed Sportradar NBA package for the persistent analytical warehouse and transient Live path. Contract SportsDataIO as an independent validation source. Use NBA.com as the official archival destination only after written confirmation that the intended commercial deep links are permitted. If the primary provider fails, serve the last validated warehouse release, mark it stale, and disable Live; do not silently switch to an unofficial endpoint.

This is a defensible technical and operational recommendation, not legal advice and not a substitute for provider order forms. The recommendation is **not approved for implementation** until provider rights and costs are confirmed in writing.

## Required product coverage

### Persistent analytics

The provider strategy must cover teams, active players, rosters, official standings, completed schedules/results, team box scores, player box scores, and shot attempts. The last item is a hard gate: event-level shot attempts, locations, outcomes, and historical retention rights must be named in the commercial agreement. “Play-by-play available” is not enough.

### Transient Live

The provider must cover today’s games, status, score, period, clock, and enough current state to produce a win-probability feature vector. The Live layer retains only a short-lived normalized state and optional compact postgame analytical summary.

### External archival links

The product should send users to the official NBA.com game, box-score, and play-by-play pages for full archival browsing. NBA.com’s public terms impose restrictions on content use and links, so the exact deep-link pattern must be confirmed in writing before implementation. Basketball-Reference may be offered as a secondary research link only where its terms permit the link and no data is scraped or mirrored.

## Candidate decision table

| Candidate | Technical fit | Published-term posture | Production decision | Cost category |
| --- | --- | --- | --- | --- |
| Sportradar NBA API | Best all-in-one fit for official schedules, stats, live, event feeds, and commercial operations | Strong technical documentation, but rights are order-form/addendum dependent | **Recommended primary** after contract | High / negotiated |
| SportsDataIO | Strong schedules, stats, live, replay, and historical products; shot depth needs confirmation | Discovery Lab is explicitly non-commercial; production rights are contract-dependent | **Recommended validator**, possible alternate primary | High / negotiated for production; $99–$149/month hobby tiers are not sufficient |
| BALLDONTLIE | Good API ergonomics, broad endpoint catalog, cheap tiers, live state | Published terms restrict redistribution, official presentation, storage, derivative databases, and competing products | Research/integration only unless separately licensed | Low public price; commercial rights uncertain |
| NBA.com endpoints via `nba_api` | Broad technical data and excellent Python client | Public NBA terms do not grant this commercial warehouse/live/comprehensive-database use | Research only | Low money; high legal/operational risk |
| Basketball-Reference | Deep archive for human browsing | Sports Reference prohibits building data products from scraping without permission | Link-only/research only | Low for browsing; licensed use unknown |

## Decision by use case

| Use case | Primary | Validation | What is not allowed by default |
| --- | --- | --- | --- |
| Teams, players, rosters | Licensed Sportradar | SportsDataIO identity/record spot checks | `nba_api` production ingestion |
| Standings, completed results | Licensed Sportradar | SportsDataIO cross-check | NBA.com scraping or unlicensed mirror |
| Team/player box scores | Licensed Sportradar | SportsDataIO game stats | Publishing raw provider payloads |
| Shot attempts | Sportradar event/shot package, only if contract explicitly includes it | SportsDataIO only if exact fields are confirmed | Deriving a shot warehouse from NBA.com endpoints without permission |
| Live score/state | Sportradar REST + Push | SportsDataIO commercial Live feed during controlled validation | BALLDONTLIE as silent commercial failover |
| Full archive browsing | NBA.com link-only, subject to written deep-link confirmation | Basketball-Reference link-only where permitted | Scraping, caching, or mirroring either archive |

## Rights classification

### Technically possible

Sportradar documents team/player/schedule/standings/game/live feeds and Push feeds. SportsDataIO documents NBA game state, stats, play-by-play, replay, and historical products. BALLDONTLIE documents teams, players, games, live state, stats, standings, box scores, lineups, and plays. `nba_api` documents access to NBA.com stats/live endpoints. NBA.com and Basketball-Reference expose human-facing archive pages.

### Permitted by published terms

The public sources support only narrow conclusions: BALLDONTLIE’s public paid tiers provide access but its terms restrict redistribution, official presentation, storage beyond reasonable application needs, and derivative commercial databases; SportsDataIO’s Discovery Lab is explicitly personal/hobby and non-commercial; NBA.com’s terms permit only narrow non-commercial/statistics uses and require attribution; Sports Reference’s data-use guidance rejects scraped derivative products. These are not production permissions for this project.

### Uncertain and requiring confirmation

For Sportradar and SportsDataIO, commercial use, raw snapshot retention, model-training rights, shot-event licensing, user exports, attribution, deep links, advertising, and post-termination retention depend on the executed agreement. NBA.com deep links to internal game pages also require confirmation because the public terms restrict linking and commercial content use. No implementation should begin on assumptions here.

## Operational policy

1. Keep source adapters behind an interface.
2. Store immutable raw snapshots only when the contract permits it.
3. Publish normalized, provenance-bearing data through the publication layer.
4. Treat provider corrections as new source snapshots and release versions.
5. Maintain source-specific freshness and coverage reports.
6. Do not let a provider failure trigger an unreviewed fallback.
7. Keep the full play-by-play archive external.

## Approval checklist

- [ ] Choose and contract the Sportradar NBA package.
- [ ] Confirm shot-attempt fields, historical depth, and retention rights.
- [ ] Confirm public display, commercial use, and attribution language.
- [ ] Confirm production property/domain and any advertising restrictions.
- [ ] Contract SportsDataIO for validation and document field-level reconciliation.
- [ ] Confirm NBA.com game-page deep-link permission.
- [ ] Approve stale-release and Live-off behavior.
- [ ] Approve monthly data budget and contingency budget.

## Research sources

- [Sportradar NBA API overview](https://developer.sportradar.com/basketball/reference/nba-overview)
- [Sportradar Push feeds](https://developer.sportradar.com/basketball/docs/nba-ig-push)
- [Sportradar Terms and Conditions](https://developer.sportradar.com/sportradar-updates/page/terms-and-conditions)
- [Sportradar Official Media Data Addendum](https://developer.sportradar.com/sportradar-updates/page/official-media-data-addendum)
- [SportsDataIO developer access](https://sportsdata.io/developers)
- [SportsDataIO NBA workflow](https://sportsdata.io/developers/workflow-guide/nba)
- [BALLDONTLIE NBA API docs](https://docs.balldontlie.io/)
- [BALLDONTLIE Terms](https://www.balldontlie.io/terms)
- [`nba_api` README](https://github.com/swar/nba_api)
- [NBA.com Terms of Use](https://api-hub.nba.com/termsofuse)
- [Sports Reference data use](https://www.sports-reference.com/data_use.html)
