import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import { StandingsPage } from "./StandingsPage";

vi.mock("../api/client", () => ({ api: { standings: vi.fn() } }));

const base = { scope: { league: null, season: "2099-00", competition: "regular", start_date: null, end_date: null }, coverage: { included_games: 1, expected_games: null, included_entities: 2, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "canonical-warehouse", source_updated_at: null, ingested_at: null, dataset_version: "phase11-standings-v1", metric_version: "team-analytics.v1", synthetic: true, contributing_source_run_count: 1 }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." } };
const metrics = { games_played: 1, wins: 1, losses: 0, home_wins: 1, home_losses: 0, away_wins: 0, away_losses: 0, last_10_wins: 1, last_10_losses: 0, last_10_sample_size: 1, points_scored: 100, points_allowed: 90, offensive_rating: null, defensive_rating: null, net_rating: 4.5, pace: null, effective_fg_percentage: null, true_shooting_percentage: null, turnover_percentage: null, offensive_rebound_percentage: null, free_throw_rate: null, conference_rank: null };
const rows = [{ team_id: "team-1", team_name: "Redwood", abbreviation: "RWD", conference: null, division: null, games_played: 1, wins: 1, losses: 0, win_percentage: 1, points_for: 100, points_against: 90, point_differential: 10, metrics, power_value: 4.5, power_basis: "recorded_net_rating" }, { team_id: "team-2", team_name: "Cinder", abbreviation: "CND", conference: null, division: null, games_played: 1, wins: 0, losses: 1, win_percentage: 0, points_for: 90, points_against: 100, point_differential: -10, metrics: { ...metrics, wins: 0, losses: 1, net_rating: -4.5 }, power_value: -4.5, power_basis: "recorded_net_rating" }];
const response = { data: { view: "standings", ordering_explanation: "Recorded Standings (derived from eligible final recorded games)", rows }, ...base };

beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.standings).mockResolvedValue(response); });
afterEach(cleanup);

const scoped = { initialEntries: ["/standings?season=2099-00&competition=regular"] };

test("renders recorded standings, synthetic coverage, team links, and honest metadata", async () => {
  render(<MemoryRouter {...scoped}><StandingsPage /></MemoryRouter>);
  expect(screen.getByRole("status")).toBeTruthy();
  expect(await screen.findByText("Synthetic recorded sample — not publishable")).toBeTruthy();
  expect(screen.getByText("Recorded Standings")).toBeTruthy();
  expect(screen.getByText("Redwood")).toBeTruthy();
  expect(screen.getByText("Derived from final recorded games. Conference and division groupings are unavailable for this recorded sample.")).toBeTruthy();
  expect(screen.queryByText(/official|playoff|prediction|odds/i)).toBeNull();
});

test("power toggle changes the view and explanatory text without changing the table", async () => {
  vi.mocked(api.standings).mockResolvedValue({ ...response, data: { ...response.data, view: "power", ordering_explanation: "Power Ordering (ordered by recorded Net Rating)" } });
  render(<MemoryRouter {...scoped}><StandingsPage /></MemoryRouter>);
  expect(await screen.findByText("Power Ordering (ordered by recorded Net Rating). Conference and division groupings are unavailable for this recorded sample.")).toBeTruthy();
  expect(screen.getByText("Redwood")).toBeTruthy();
});

test("requires an explicit season and competition", () => {
  render(<MemoryRouter><StandingsPage /></MemoryRouter>);
  expect(screen.getByText("Select both a season and competition to view derived standings.")).toBeTruthy();
  expect(api.standings).not.toHaveBeenCalled();
});

test("scope changes request the existing standings API", async () => {
  render(<MemoryRouter><StandingsPage /></MemoryRouter>);
  fireEvent.change(screen.getByLabelText("Standings season"), { target: { value: "2099-00" } });
  fireEvent.change(screen.getByLabelText("Standings competition"), { target: { value: "regular" } });
  await waitFor(() => expect(api.standings).toHaveBeenCalledWith({ season: "2099-00", competition: "regular", view: "standings" }));
});

test("does not imply official standings", async () => {
  render(<MemoryRouter {...scoped}><StandingsPage /></MemoryRouter>);
  expect(await screen.findByText("Recorded Standings")).toBeTruthy();
  expect(screen.queryByText(/official|playoff|prediction|odds/i)).toBeNull();
});

test("renders an API error", async () => {
  vi.mocked(api.standings).mockRejectedValue(new Error("Standings unavailable"));
  render(<MemoryRouter {...scoped}><StandingsPage /></MemoryRouter>);
  expect(await screen.findByText("Standings unavailable")).toBeTruthy();
});
