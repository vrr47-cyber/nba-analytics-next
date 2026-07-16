# NBA Analytics Coverage Rules

Status: Phase 0 — publication gates

## Core rule

No number is published as a complete season, rank, forecast, or model output until its coverage and qualification requirements pass.

## Coverage states

- `complete`: expected population and time window are covered within the approved tolerance.
- `partial_labeled`: usable for explicitly labeled partial-sample views only.
- `stale`: data may be retained but cannot be presented as fresh.
- `blocked`: validation or provenance failure prevents publication.
- `unavailable`: required source or calculation does not exist.

## Minimum publication requirements

| Output | Minimum requirement |
| --- | --- |
| Season team statistic | All eligible team games in the selected window, or a documented approved tolerance, with no unresolved material gaps. |
| Season player statistic | Player game coverage and roster identity coverage satisfy the season rule; games/minutes qualification is visible. |
| Leaderboard | Comparable eligible population, explicit threshold, and incomplete values excluded rather than zero-filled. |
| Shot analytics | Shot coverage passes the player/team eligibility rule; expected values include model version and sample size. |
| Official standings | Sourced standings snapshot with source timestamp and competition context. |
| Power ranking | Complete comparable team population and a published rating version. Must be visually distinct from official standings. |
| Playoff forecast | Remaining-schedule coverage and forecast inputs pass validation; timestamp, model version, and limitations are shown. |
| Live probability | Live state is recent enough for the model, required features are present, and source freshness is shown. |

## Qualification policy

Qualification thresholds are named rules, not hidden UI filters. Examples include minimum games, minimum minutes, minimum shot attempts, and complete-team population. Each leaderboard displays the rule used.

## Staleness

Freshness thresholds are domain-specific and configured in release policy. A stale record may be shown only with a stale label and never as current. A stale forecast is withheld from the default forecast surface.

## Missing data

Missing values remain null. They are not converted to zero, ranked as worst, or silently imputed. Imputation is allowed only inside documented model features and must be recorded.

## Release gate

Before a batch is public:

1. validate source schema;
2. validate entity identity and duplicates;
3. compare expected versus observed coverage;
4. run truth fixtures and metric checks;
5. generate coverage report;
6. run publication rules;
7. record release ID, source snapshots, calculation versions, and operator/job identity.

## User-facing coverage panel

Explore and relevant detail pages must expose team-game coverage, player-game coverage, roster coverage, shot coverage, standings freshness, forecast status, and live-provider status. The panel explains blocked or partial states in plain language.
