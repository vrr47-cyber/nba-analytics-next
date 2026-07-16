# NBA Analytics Product Specification

Status: Phase 0 — product definition
Owner: NBA Analytics project
Last updated: 2026-07-16

## Product definition

NBA Analytics is a stats-first NBA intelligence platform. It helps users understand:

- which teams are strongest and why;
- which players are producing and how efficiently;
- where players and teams shoot;
- whether shot outcomes are above or below expectation;
- how team strength changes over time;
- what playoff outcomes are plausible; and
- how win probability changes during an active game.

The product owns analysis and interpretation. External providers own complete schedules, historical box-score archives, transaction histories, news, and full play-by-play browsing.

## Product boundary

The first release is not a replacement for NBA.com, Basketball Reference, a full game archive, a generic scoreboard, or a collection of manual calculators. Historical games are supporting evidence accessed through team recent games, player logs, compact live summaries, or outbound links.

## Product principles

1. Accuracy before visual polish.
2. Every published number is traceable to source, season, competition, date range, sample size, coverage, and calculation version.
3. Partial samples are never described as full-season results.
4. Rankings require a valid comparison population and qualification thresholds.
5. Model probabilities are estimates, not guarantees.
6. Manual inputs belong in Labs, not in the primary product flow.
7. Coverage and provenance are product UI, not hidden implementation details.
8. Each page answers a real basketball question.

## Primary navigation

Explore, Teams, Players, Shot Analytics, Standings & Power, Playoff Forecast, Live, Methodology.

Secondary navigation: Labs, Data Status, About.

There is no general Games page in the primary navigation.

## Page questions

| Surface | Question it must answer |
| --- | --- |
| Explore | What is happening in the league, and which signals deserve attention? |
| Teams | How good is this team and why? |
| Players | What is this player producing and how? |
| Shot Analytics | What shots does this player take, and how well do they convert them? |
| Standings & Power | Which teams are strongest under official standings versus the model rating? |
| Playoff Forecast | What outcomes are plausible, and how complete is the forecast input? |
| Live | How is win probability changing in an active game? |
| Methodology | How are sources, metrics, qualification, and models defined? |
| Data Status | What is covered, stale, missing, or blocked from publication? |
| Labs | Which manual or experimental tools are explicitly non-production? |

## Explore requirements

Explore is an analytical home, not a marketing page. It should show season and competition context, update time, coverage status, league snapshot cards, qualified player leaders, shot-intelligence modules, standings versus power, playoff outlook, live games, and the mandatory coverage panel.

Every metric card must expose metric definition, source context, sample size, coverage state, qualification rule, calculation version, and a link to methodology when applicable.

## Teams requirements

The team directory is a compact analytical table with record, conference rank, ORtg, DRtg, Net Rating, pace, eFG%, recent form, and power rank. Team detail answers how good the team is, how it plays, and its outlook. It may show a roster, supported lineup label, advanced metrics, trends, shooting profile, recent and upcoming games, and playoff outlook only when corresponding data contracts pass publication gates.

## Players requirements

The player directory is season-scoped by default and supports team, position, minimum games, minimum minutes, and search filters. Player detail answers what the player produces, how efficiently, and how results are generated. It may show traditional stats, safe early advanced metrics, shot profile, actual-versus-expected shooting, game logs, and trend charts when coverage permits.

## Live requirements

Live is the one intentionally transient component. It fetches current scoreboard and selected-game state, normalizes it, calculates a win-probability response, caches the active session briefly, and returns it to the frontend. The system does not become a permanent live-feed archive. After a game ends, only a compact analytical summary may be retained: game ID, teams, final score, timestamp, probability timeline, largest swing, and model version.

## Non-goals for Phase 0

- No backend implementation.
- No live provider integration.
- No production model training.
- No full schedule or game archive.
- No news or transaction system.
- No authentication requirement.
- No broad microservice platform.
- No realistic placeholder NBA statistics outside the clearly labeled `design-prototype` branch.
