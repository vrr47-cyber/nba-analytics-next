import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import { ShotsPage } from "./ShotsPage";

vi.mock("../api/client", () => ({ api: { shotSummary: vi.fn(), shotZones: vi.fn() } }));

const base = { scope: { league: null, season: null, competition: null, start_date: null, end_date: null }, coverage: { included_games: 1, expected_games: 1, included_entities: 8, expected_entities: 8, coverage_ratio: 1, is_complete: true, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "fixture", source_updated_at: null, ingested_at: null, dataset_version: "phase10a-shots-v1", metric_version: "shot-analytics.v1", synthetic: true, contributing_source_run_count: 1 }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." } };
const summary = { attempts: 8, makes: 4, field_goal_attempts: 6, field_goal_makes: 3, three_point_attempts: 2, three_point_makes: 1, fg_percentage: 0.5, three_point_percentage: 0.5, effective_fg_percentage: 0.583, actual_points: 9, average_distance: 14.4, expected_fg_percentage: null, expected_points: null, zone_distribution: [{ key: "paint", attempts: 2, share: 0.25 }], shot_type_distribution: [{ key: "two_point", attempts: 4, share: 0.5 }, { key: "free_throw", attempts: 2, share: 0.25 }], coordinates: [] };

beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.shotSummary).mockResolvedValue({ data: summary, ...base }); vi.mocked(api.shotZones).mockResolvedValue({ data: baseZones, ...base }); });
afterEach(cleanup);
const baseZones = [{ key: "paint", attempts: 2, share: 0.25 }];

test("renders shot metrics, synthetic warning, tables, and honest expected values", async () => {
  render(<MemoryRouter><ShotsPage /></MemoryRouter>);
  expect(await screen.findByText("Synthetic recorded sample — not publishable")).toBeTruthy();
  expect(screen.getByText("Shot Analytics")).toBeTruthy();
  expect(screen.getAllByText("Attempts").length).toBeGreaterThan(0);
  expect(screen.getByText("Expected FG%")).toBeTruthy();
  expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  expect(screen.getByText("Insufficient data for a zone heatmap (minimum 20 attempts).")).toBeTruthy();
  expect(screen.getByText("Methodology")).toBeTruthy();
});

test("renders loading and error states", async () => {
  vi.mocked(api.shotSummary).mockImplementation(() => new Promise(() => undefined));
  render(<MemoryRouter><ShotsPage /></MemoryRouter>);
  expect(screen.getByRole("status")).toBeTruthy();
  cleanup();
  vi.mocked(api.shotSummary).mockRejectedValue(new Error("Shot API unavailable"));
  vi.mocked(api.shotZones).mockRejectedValue(new Error("Shot API unavailable"));
  render(<MemoryRouter><ShotsPage /></MemoryRouter>);
  expect(await screen.findByText("Shot API unavailable")).toBeTruthy();
});

test("renders an empty state without fabricating metrics", async () => {
  vi.mocked(api.shotSummary).mockResolvedValue({ data: { ...summary, attempts: 0, makes: 0 }, ...base });
  render(<MemoryRouter><ShotsPage /></MemoryRouter>);
  expect(await screen.findByText("There are no validated shot observations in this scope.")).toBeTruthy();
  expect(screen.queryByText("0.0%")).toBeNull();
});
