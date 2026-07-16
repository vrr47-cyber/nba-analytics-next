# NBA Analytics Source Strategy

Status: Phase 0 — provider decision incorporated
Last reviewed: 2026-07-16

## Governing rule

The product owns analysis and interpretation. External providers own the complete NBA game archive. We will not build a second NBA.com or Basketball-Reference archive.

## Recommendation

- **Primary persistent data:** contract a commercial Sportradar NBA API package with explicit rights for permanent internal storage of the licensed historical feed, production display on the named property, completed schedules/results, standings, team/player box scores, and event/shot-attempt data if the exact shot fields are included in the order form.
- **Secondary truth validation:** contract SportsDataIO's commercial Leagues API or Vault for independent score, date, standings, team-game, and player-game checks. It is a validation source, not an automatic failover or a second public database.
- **Transient live data:** use Sportradar's real-time NBA REST feeds plus Push Clock/Events/Statistics if the commercial order form covers live fan-facing display. Normalize the current state, cache it briefly in Redis, and discard the raw stream after the compact-summary retention window.
- **Official archival links:** link users to NBA.com game/box-score/play-by-play pages only after written confirmation that the intended deep links are permitted for this product. Until then, expose an NBA.com home or team link and label the deep-link capability blocked. Do not scrape or mirror NBA.com.
- **Fallback:** for persistent analytics, serve the last validated warehouse release with a stale label; stop new publication when coverage expires. For Live, disable the module when Sportradar is unavailable. SportsDataIO may be activated only as a pre-approved, contractually licensed temporary source; never silently switch to `nba_api`, NBA.com web endpoints, or Basketball Reference.

## Three-way status vocabulary

- **Technically possible:** public documentation demonstrates the endpoint or data shape.
- **Permitted by published terms:** the public terms or a clearly described commercial tier expressly permit the intended use. A sales page alone is not a license to redistribute.
- **Uncertain / requires confirmation:** the API works or a capability is described, but storage, raw-response redistribution, deep linking, commercial display, shot-level fields, or derivative-database rights are not clear. Legal/provider confirmation is required.

## Candidate comparison

### 1. Sportradar NBA API — preferred production candidate

| Field | Assessment |
| --- | --- |
| Datasets/endpoints | League hierarchy, teams, active rosters, player profiles, seasons, schedules, standings, rankings, game summary, game boxscore, player/team stats, play-by-play, injuries, daily change log, live clock, live events, and live statistics. Event feeds expose event categories including shots; exact shot coordinates/attempt fields must be confirmed in the product package. |
| Historical depth | Current season plus prior seasons available according to the licensed product; the public terms define “Complete History” as current plus all available prior seasons, but the order form controls what is actually delivered. |
| Live capability | Real-time NBA data; real-time customers can use Push Clock, Push Events, and Push Statistics. Public docs describe live event and positional data. |
| Authentication | Account and API key in the `x-api-key` header. |
| Published rate limits | Public package pages describe Standard NBA at 25,000 requests per rolling 30 days and Real-time NBA at 2,000,000; Push feeds have no connection-count restriction. Contract-specific limits and fair-use terms control. |
| Reliability | Strongest candidate: official NBA data-provider positioning, on-venue statisticians, daily change log, validation workflow, failover documentation, and commercial support/SLA options. Still requires monitoring and reconciliation. |
| Licensing / redistribution | Not granted by endpoint access. Public terms restrict use to licensed Properties, prohibit unapproved redistribution/derivative use, require retaining attribution notices, and make official-data rights subject to the order form/addendum. |
| Commercial use | Possible under a negotiated commercial agreement for the named site and use case; not established by the free trial. Advertising, sponsorship, marks, advanced statistics, and public exports need explicit confirmation. |
| Permanent storage | Technically supported for reproducibility; permitted only to the extent the order form grants archival/internal retention. Confirm raw snapshots, normalized tables, model training, backup retention, and post-termination deletion. |
| Raw response redistribution | Treat as prohibited unless expressly licensed. Publish only derived, publication-approved values and links. |
| Attribution | Preserve provider, league, and any required byline/attribution. Exact wording is order-form dependent. |
| Cost | Enterprise/contact-sales; budget category: **high / negotiated**. Public pages advertise a trial but do not publish production NBA pricing. |
| Python integration | Good HTTP/JSON fit, versioned REST API, Postman/schema resources, and straightforward adapter implementation. No official Python SDK is required. |
| Operational risks | Contract scope, feed versioning, provider continuity, rights to shot/tracking fields, latency, correction semantics, and cost. Do not assume every “NBA” endpoint is included in one package. |
| Production suitability | **Yes, preferred**, contingent on a signed agreement that covers this exact product. |

Evidence: [NBA API overview](https://developer.sportradar.com/basketball/reference/nba-overview), [NBA API basics](https://developer.sportradar.com/basketball/docs/nba-ig-api-basics), [Push feeds](https://developer.sportradar.com/basketball/docs/nba-ig-push), [Sportradar terms](https://developer.sportradar.com/sportradar-updates/page/terms-and-conditions), [Official Media Data Addendum](https://developer.sportradar.com/sportradar-updates/page/official-media-data-addendum).

### 2. SportsDataIO — preferred independent validator and possible commercial alternative

| Field | Assessment |
| --- | --- |
| Datasets/endpoints | NBA schedules, scores, game state, standings, team/player season and game stats, play-by-play, injuries, lineups, and related feeds. Public NBA workflow documentation shows `Game`, `ScoreBasic`, `PlayerGame`, `TeamGame`, `PlayerSeason`, `TeamSeason`, and `Play`. Public docs do not establish a complete shot-attempt/shot-coordinate product; require a field-level confirmation. |
| Historical depth | Vault advertises 10+ years and prior-season retrieval through production endpoints or archive endpoints, subject to access. |
| Live capability | Leagues API advertises real-time live coverage; public NBA workflow says in-game game state and live stats typically trail TV by about 15–20 seconds. Discovery Lab is next-day delayed and is not suitable for Live. |
| Authentication | API key, documented in query parameter or `Ocp-Apim-Subscription-Key` header. |
| Published rate limits | Free trial has a small daily limit; Discovery Lab has 100–1,000 calls/day by tier; Leagues API advertises unlimited calls; exact commercial contract limits and fair use still require confirmation. |
| Reliability | Mature REST shape, real-time/archival product split, replay tools, and commercial SLA/support options. Less attractive than Sportradar as the NBA primary because public docs do not establish official NBA data rights or shot depth. |
| Licensing / redistribution | Discovery Lab explicitly says it is not licensed for commercial redistribution. Commercial Leagues/Vault terms are contract-driven; storage, raw redistribution, derivative database, and public display rights require the order form. |
| Commercial use | Possible only through commercial agreement. Discovery Lab is personal/hobby use and is not a production commercial license. |
| Permanent storage | Technically possible through Vault/historical access; permission depends on commercial terms. Do not store Discovery Lab as a production warehouse. |
| Raw response redistribution | Treat as prohibited unless expressly licensed. Store only controlled raw snapshots for internal reproducibility if the contract permits. |
| Attribution | Not established in the public developer pages; require contract language. |
| Cost | Discovery Lab: public tiers of $99/month or $149/month, but delayed and non-commercial. Production Leagues/Vault: **high / negotiated**. |
| Python integration | Good REST/JSON/OpenAPI fit; public OpenAPI files exist. Public integration tooling is strongest for C# and Node.js, but Python HTTP integration is straightforward. |
| Operational risks | Scrambled trial data is not valid for analysis; Discovery Lab is delayed/non-commercial; field coverage and retention rights vary by package; independent provider may disagree with Sportradar. |
| Production suitability | **Yes as secondary validator; possible primary alternative after contract review.** Not suitable as production on Discovery Lab. |

Evidence: [developer access and pricing tiers](https://sportsdata.io/developers), [NBA workflow](https://sportsdata.io/developers/workflow-guide/nba), [API documentation](https://sportsdata.io/developers/apis), [NBA data dictionary](https://sportsdata.io/developers/data-dictionary/nba), [OpenAPI resources](https://sportsdata.io/developers/sports-data-open-api-swagger-files).

### 3. BALLDONTLIE — useful research/integration candidate, not production default

| Field | Assessment |
| --- | --- |
| Datasets/endpoints | Teams, players, active players, games, realtime game state, player game stats, season/team averages, advanced stats, standings, lineups, plays, box scores, injuries, and leaders. Public docs say data spans 1946–current and show period, clock/status, scores, player stats, and play-by-play. Public docs do not establish a shot-attempt dataset with the detail needed for shot quality. |
| Historical depth | Broad historical claim to 1946–current; endpoint-level completeness and correction history need validation. |
| Live capability | In-progress games and player stats are described as realtime; no guaranteed latency. |
| Authentication | API key in `Authorization` header; account required. |
| Published rate limits | Free 5 requests/minute, ALL-STAR 60/minute, GOAT 600/minute; paid plans listed at $9.99/month and $39.99/month for NBA tiers. |
| Reliability | Easy to integrate and useful for prototypes; terms state data is aggregated from third parties, best-effort, not guaranteed official, complete, accurate, or timely. |
| Licensing / redistribution | Terms prohibit reselling/redistributing API/data without written permission, prohibit presenting data as official league statistics, restrict caching/storing beyond reasonable application needs without consent, and prohibit derivative commercial databases. |
| Commercial use | The paid price is not a commercial redistribution license. The terms also prohibit building a competing product/service; legal/provider confirmation would be required. |
| Permanent storage | Not permitted by the published terms beyond reasonable application needs without consent; not acceptable for the warehouse without written permission. |
| Raw response redistribution | Not permitted without express written permission. |
| Attribution | No general public attribution grant was identified; lack of an attribution clause is not permission to omit source or league attribution. |
| Cost | **Low** for personal research ($0–$39.99/month public tiers); commercial rights unknown. |
| Python integration | Good; public docs include Python examples and a Python SDK. |
| Operational risks | Third-party aggregation, no official-league guarantee, best-effort live data, strict storage/redistribution terms, endpoint tier gating, and possible prohibition on competing products. |
| Production suitability | **Research/integration only unless a written commercial license is obtained.** |

Evidence: [BALLDONTLIE API docs](https://docs.balldontlie.io/), [account tiers and limits](https://docs.balldontlie.io/), [Terms of Service](https://www.balldontlie.io/terms).

### 4. NBA.com Stats/Live endpoints via `nba_api` — technically powerful, legally and operationally unsuitable as production source

| Field | Assessment |
| --- | --- |
| Datasets/endpoints | `nba_api` exposes NBA.com stats endpoints and live scoreboard/live-game endpoints, including schedules, standings, player/team stats, play-by-play, and shot/stat dashboard-shaped data. |
| Historical depth | Technically broad and long-running, depending on endpoint. The client maps undocumented/unstable NBA.com endpoints; NBA.com does not publish endpoint change/deprecation information. |
| Live capability | Technically available through `nba_api.live.nba.endpoints.scoreboard` and related endpoints. |
| Authentication | Public requests may work without an API key today; no production credential or SLA is provided. |
| Published rate limits | No official public rate-limit/SLA commitment identified. Treat limits as unknown and avoid load. |
| Reliability | Useful for notebooks, truth spot checks, and research. Endpoint changes, bot controls, downtime, and lack of support make it fragile. |
| Licensing / redistribution | NBA.com Terms state NBA content is owned/licensed, restrict reproduction and public/commercial use without written permission, and limit NBA Statistics to prominent attribution and non-commercial/private/news uses. The terms also restrict comprehensive regularly updated databases and live/near-live/play-by-play uses without express consent. |
| Commercial use | **Not permitted by the public terms for this product shape.** Written NBA permission would be required. |
| Permanent storage | Not safe to assume. The public terms do not grant the warehouse/archive/model-training rights needed here. |
| Raw response redistribution | Not permitted without written permission. |
| Attribution | NBA.com attribution is required when NBA Statistics are used under the terms, but attribution does not cure the commercial/comprehensive-database restrictions. |
| Cost | **Low monetary cost / high legal and operational risk.** The `nba_api` package is MIT, but that license covers the client, not NBA data. |
| Python integration | Excellent via the community Python client; this is precisely why it is tempting. |
| Operational risks | Undocumented endpoints, no SLA/rate limits, endpoint churn, blocking, provider terms, and mistaken assumption that API accessibility equals permission. |
| Production suitability | **No**, unless a separate written license/permission is obtained. Research-only. |

Evidence: [`nba_api` README and terms warning](https://github.com/swar/nba_api), [NBA.com Terms of Use](https://api-hub.nba.com/termsofuse).

### 5. Basketball-Reference / Sports-Reference — archival destination and research reference only

| Field | Assessment |
| --- | --- |
| Datasets/endpoints | Official website pages provide historical player/team/game logs, box scores, schedules, standings, and play-by-play-adjacent archive context. No approved public production API was identified in this pass. |
| Historical depth | Excellent historical depth for browsing and research. |
| Live capability | Not a live provider. |
| Authentication | No API credential for normal browsing; account/Stathead products may have separate terms. |
| Published rate limits | No production API limit identified; bot-traffic guidance and site rules apply. |
| Reliability | Strong archival reference, but not a machine-data SLA and not a source for current live state. |
| Licensing / redistribution | Sports Reference's data-use page says not to create websites/tools from scraped data without permission and prohibits scraping beyond permitted uses. |
| Commercial use | Not permitted for scraped/republished product data without permission. |
| Permanent storage | Do not store scraped pages or derivative databases. Store only user-directed URLs and internal notes about the link. |
| Raw response redistribution | Not permitted. |
| Attribution | Cite/link Basketball-Reference when a user is directed there; exact commercial display rights require permission. |
| Cost | **Low for link-only browsing; unknown/paid for Stathead or licensed use.** |
| Python integration | Scrapers exist in the ecosystem, but that does not establish permission or a supported API. |
| Operational risks | Scraping restrictions, bot controls, site structure changes, no live feed, and derivative-database restrictions. |
| Production suitability | **Archival link destination and private research reference only.** |

Evidence: [Sports Reference data use](https://www.sports-reference.com/data_use.html), [Sports Reference terms](https://www.sports-reference.com/termsofuse.html), [Basketball-Reference about](https://www.basketball-reference.com/about/).

## Capability matrix

| Requirement | Sportradar | SportsDataIO | BALLDONTLIE | NBA.com / `nba_api` | Basketball-Reference |
| --- | --- | --- | --- | --- | --- |
| Teams / active players | Yes | Yes | Yes | Yes technically | Browse only |
| Rosters | Yes | Yes | Tier-dependent | Yes technically | Browse only |
| Standings | Yes | Yes | GOAT | Yes technically | Browse only |
| Completed schedules/results | Yes | Yes | Yes | Yes technically | Browse only |
| Team/player box scores | Yes | Yes | GOAT | Yes technically | Browse only |
| Shot attempts | Event/shot capability must be licensed/confirmed | Must confirm exact feed | Not established publicly | Technically available, not permitted for this use | No |
| Live today/status/score/clock | Yes, REST + Push | Yes on commercial Leagues API | Yes, best-effort | Yes technically | No |
| Permanent warehouse | Contract-dependent | Contract-dependent | Not under public terms | Not under public terms | No |
| Raw redistribution | Contract-dependent, assume no | Contract-dependent, assume no | No without permission | No without permission | No |
| Production recommendation | Primary | Validator / alternate | Research only | Research only | Links/research only |

## Fallback design

Fallback is a release policy, not a blind provider switch. If the primary feed is unavailable, the system serves the last validated release with a stale status for persistent pages. It withholds new rankings, forecasts, and shot outputs when freshness or coverage gates expire. Live is disabled rather than backed by an unlicensed feed. SportsDataIO can be activated as a temporary fallback only after a contract and field-level permission review.

## Approval gates before implementation

Obtain written confirmation for: shot-attempt fields and historical depth; permanent raw snapshot retention; derived metric and model-training rights; public display and export rights; attribution language; production domains/Properties; advertising or commercial use; user-facing NBA.com deep links; and post-termination deletion/archival obligations.
