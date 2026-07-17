import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import { TeamsPage } from "./TeamsPage";

const response = {
  data: [{ id: "team-1", name: "Fixture Redwood", abbreviation: "RED", conference: null, metrics: { games_played: 1, wins: 1, losses: 0, home_wins: 1, home_losses: 0, away_wins: 0, away_losses: 0, last_10_wins: 1, last_10_losses: 0, last_10_sample_size: 1, points_scored: 100, points_allowed: 90, offensive_rating: null, defensive_rating: null, net_rating: null, pace: null, effective_fg_percentage: null, true_shooting_percentage: null, turnover_percentage: null, offensive_rebound_percentage: null, free_throw_rate: null, conference_rank: null } }], scope: { league: null, season: null, competition: null, start_date: null, end_date: null }, coverage: { included_games: 1, expected_games: null, included_entities: 1, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "canonical-warehouse", source_updated_at: null, ingested_at: null, dataset_version: null, metric_version: "team-analytics.v1", synthetic: true, contributing_source_run_count: 1 }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." },
};

vi.mock("../api/client", () => ({ api: { teams: vi.fn(() => Promise.resolve(response)) } }));

beforeEach(() => vi.clearAllMocks());

test("teams directory shows synthetic warning and unavailable metrics", async () => {
  render(<MemoryRouter><TeamsPage /></MemoryRouter>);
  expect(await screen.findByText("Synthetic recorded sample — not publishable")).toBeTruthy();
  expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  expect(screen.queryByText("Power Ranking")).toBeNull();
});
