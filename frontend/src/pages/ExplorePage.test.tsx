import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { ExplorePage } from "./ExplorePage";

const response = { data: { featured_teams: { data: [], coverage: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "canonical", source_updated_at: null, ingested_at: null, dataset_version: null, metric_version: null, synthetic: true, contributing_source_run_count: 1 } }, featured_players: { data: [], coverage: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "canonical", source_updated_at: null, ingested_at: null, dataset_version: null, metric_version: null, synthetic: true, contributing_source_run_count: 1 } }, recent_games: { data: [], coverage: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "canonical", source_updated_at: null, ingested_at: null, dataset_version: null, metric_version: null, synthetic: true, contributing_source_run_count: 1 } }, coverage_summary: { teams: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, players: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, recent_games: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." } } }, scope: { league: null, season: null, competition: null, start_date: null, end_date: null }, coverage: { included_games: 0, expected_games: null, included_entities: 0, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "composed-canonical-warehouse", source_updated_at: null, ingested_at: null, dataset_version: null, metric_version: null, synthetic: true, contributing_source_run_count: null }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." } };
vi.mock("../api/client", () => ({ api: { explore: vi.fn(() => Promise.resolve(response)) } }));
beforeEach(() => vi.clearAllMocks());
afterEach(cleanup);

test("Explore renders compact sections and synthetic coverage", async () => {
  render(<MemoryRouter><ExplorePage /></MemoryRouter>);
  expect(await screen.findByText("Synthetic recorded sample — not publishable")).toBeTruthy();
  expect(screen.getByText("Featured Teams")).toBeTruthy();
  expect(screen.getByText("Featured Players")).toBeTruthy();
  expect(screen.getByText("Recent Games")).toBeTruthy();
  expect(screen.getByText("Methodology")).toBeTruthy();
  expect(screen.queryByText(/ranking|leaders|shot analytics/i)).toBeNull();
});

function LocationProbe() { const location = useLocation(); return <output data-testid="location">{location.pathname}{location.search}</output>; }

test("Explore search navigates to the existing Teams route", async () => {
  render(<MemoryRouter><ExplorePage /><LocationProbe /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Explore search"), { target: { value: "Fixture" } });
  fireEvent.click(screen.getByRole("button", { name: "Search Teams" }));
  expect(screen.getByTestId("location").textContent).toBe("/teams?search=Fixture");
});
