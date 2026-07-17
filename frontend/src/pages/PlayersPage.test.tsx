import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, test, vi } from "vitest";
import { PlayersPage } from "./PlayersPage";

const response = { data: [{ id: "player-1", name: "Fixture Player", position: "SG", current_team_id: "team-1", current_team_name: "Fixture Team", team_attribution: { state: "single_team", team_ids: ["team-1"], team_names: ["Fixture Team"] }, metrics: { games_available: 2, games_played: 1, games_started: null, non_participation_count: 1, total_minutes: 30, minutes_per_game: 30, points: 20, rebounds: 4, assists: 5, steals: 1, blocks: 1, turnovers: 2, fouls: 2, points_per_game: 20, rebounds_per_game: 4, assists_per_game: 5, steals_per_game: 1, blocks_per_game: 1, field_goal_percentage: null, three_point_percentage: null, free_throw_percentage: null, effective_fg_percentage: null, true_shooting_percentage: null, points_per_36: 24, rebounds_per_36: 4.8, assists_per_36: 6, steals_per_36: 1.2, blocks_per_36: 1.2, three_point_attempt_rate: null, free_throw_rate: null } }], scope: { league: null, season: null, competition: null, start_date: null, end_date: null }, coverage: { included_games: 2, expected_games: null, included_entities: 1, expected_entities: null, coverage_ratio: null, is_complete: false, is_publishable: false, reason: "Synthetic recorded sample — not publishable." }, provenance: { source: "canonical-warehouse", source_updated_at: null, ingested_at: null, dataset_version: null, metric_version: "player-analytics.v1", synthetic: true, contributing_source_run_count: 1 }, publication: { publishable: false, code: "synthetic_fixture", reason: "Synthetic recorded sample — not publishable." } };
vi.mock("../api/client", () => ({ api: { players: vi.fn(() => Promise.resolve(response)) } }));
beforeEach(() => vi.clearAllMocks());

test("players directory uses explicit per-game headings and synthetic warning", async () => {
  render(<MemoryRouter><PlayersPage /></MemoryRouter>);
  expect(await screen.findByText("Synthetic recorded sample — not publishable")).toBeTruthy();
  expect(screen.getByText("Points / game")).toBeTruthy();
  expect(screen.getByText("Minutes / game")).toBeTruthy();
  expect(screen.queryByText("League leaders")).toBeNull();
});
