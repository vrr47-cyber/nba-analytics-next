import { cleanup, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";
import { api } from "../api/client";
import type { PlayerDetail } from "../api/types";
import { PlayerShotProfilePage } from "./PlayerShotProfilePage";

vi.mock("../api/client", () => ({ api: { playerShots: vi.fn(), player: vi.fn(), shotZones: vi.fn() } }));

const base = { scope: { league: null, season: null, competition: null, start_date: null, end_date: null }, coverage: { included_games: 1, expected_games: 1, included_entities: 8, expected_entities: 8, coverage_ratio: 1, is_complete: true, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "fixture", source_updated_at: null, ingested_at: null, dataset_version: "phase10a-shots-v1", metric_version: "shot-analytics.v1", synthetic: true, contributing_source_run_count: 1 }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." } };
const profile = { player_id: "player-1", summary: { attempts: 2, makes: 1, field_goal_attempts: 2, field_goal_makes: 1, three_point_attempts: 1, three_point_makes: 0, fg_percentage: 0.5, three_point_percentage: 0, effective_fg_percentage: 0.5, actual_points: 2, average_distance: 10, expected_fg_percentage: null, expected_points: null, zone_distribution: [], shot_type_distribution: [{ key: "two_point", attempts: 2, share: 1 }], coordinates: [{ x: 4, y: 3, result: "made", shot_type: "two_point" }, { x: 16, y: 4, result: "missed", shot_type: "two_point" }] } };
const player = { id: "player-1", name: "Fixture Player", position: "SG", current_team_id: "team-1", current_team_name: "Fixture Team", team_attribution: { state: "single_team", team_ids: ["team-1"], team_names: ["Fixture Team"] }, metrics: {} } as unknown as PlayerDetail;

beforeEach(() => { vi.clearAllMocks(); vi.mocked(api.playerShots).mockResolvedValue({ data: profile, ...base }); vi.mocked(api.player).mockResolvedValue({ data: player, ...base }); vi.mocked(api.shotZones).mockResolvedValue({ data: [{ key: "paint", attempts: 2, share: 1 }], ...base }); });
afterEach(cleanup);

test("renders player identity, attribution, shot chart, coverage, and methodology", async () => {
  render(<MemoryRouter initialEntries={["/shots/players/player-1"]}><Routes><Route path="/shots/players/:playerId" element={<PlayerShotProfilePage />} /></Routes></MemoryRouter>);
  expect(await screen.findByText("Fixture Player")).toBeTruthy();
  expect(screen.getByText("Current team:")).toBeTruthy();
  expect(screen.getByRole("img", { name: "Shot chart using normalized coordinates" })).toBeTruthy();
  expect(screen.getByText("Synthetic recorded sample — not publishable")).toBeTruthy();
  expect(screen.getByText("Insufficient data for a zone heatmap (minimum 20 attempts).")).toBeTruthy();
  expect(screen.getByText("Review coverage and provenance")).toBeTruthy();
});

test("shows empty state when the player has no shots", async () => {
  vi.mocked(api.playerShots).mockResolvedValue({ data: { ...profile, summary: { ...profile.summary, attempts: 0 } }, ...base });
  render(<MemoryRouter initialEntries={["/shots/players/player-1"]}><Routes><Route path="/shots/players/:playerId" element={<PlayerShotProfilePage />} /></Routes></MemoryRouter>);
  expect(await screen.findByText("No validated shot observations are available for this player and scope.")).toBeTruthy();
});
