# NBA Analytics Model Plan

Status: Phase 0 — model plan

## Modeling principles

- Models are subordinate to data quality and publication rules.
- Every model has a registry entry, version, feature snapshot, training cutoff, evaluation report, calibration report, and limitations.
- Model outputs are estimates, not guarantees.
- A model cannot make an ineligible statistic publishable.
- Offline research artifacts are separate from production inference artifacts.

## Planned model families

### Pre-game win probability

Baseline: transparent logistic or gradient-boosted model using team rating, location, rest, opponent strength, recent form, and injury availability only when reliable. Evaluate calibration, Brier score, log loss, reliability by probability bucket, and performance by season.

### Live win probability

Use normalized score, clock, period, possession/state features, pre-game strength, and live context. Start with a transparent baseline and compare against more complex models. Expose model version, generated time, source freshness, calibration information, and limitations.

### Elo / power rating

Maintain a dynamic rating updated after completed games. Document margin, location, opponent strength, season transitions, and update schedule. Show it separately from official standings.

### Player impact

Begin with regularized regression or another interpretable baseline. Do not call a value player impact unless the target, training data, confounders, and uncertainty are documented.

### Shot quality

Estimate expected FG% or expected points from shot location, defender/context features when coverage supports them. Publish actual-versus-expected only for qualified coverage and with model version and sample size.

### Playoff simulation

Use team strength, remaining schedule, matchup adjustments, and supported availability inputs. Run enough simulations for stable estimates and disclose assumptions. Withhold the forecast when remaining-schedule coverage is incomplete.

## Evaluation requirements

Every model requires train/validation/test separation, leakage checks, temporal validation, baseline comparison, calibration analysis, subgroup or context slices, data coverage summary, and a human-readable limitations section.

## Publication requirements

A model prediction response includes model version, feature snapshot, generated timestamp, source coverage, calibration summary, uncertainty where available, and limitations. Frontend charts do not compute or reinterpret model outputs.

## Rollout stages

1. Truth fixtures and deterministic metric baselines.
2. Offline baseline models.
3. Temporal evaluation and calibration.
4. Shadow inference with no public exposure.
5. Publication behind coverage gates.
6. Monitoring and versioned rollback.
