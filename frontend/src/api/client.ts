import type { Envelope, ExploreData, PlayerDetail, PlayerRecentGame, PlayerShotProfile, PlayerSplit, PlayerSummary, PlayerTrendPoint, RecentGame, RosterEntry, Season, ShotAnalyticsSummary, ShotDistribution, StandingsData, Status, TeamDetail, TeamSummary, TrendPoint } from "./types";

const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
async function request<T>(path: string): Promise<T> { const response = await fetch(`${base}${path}`); if (!response.ok) throw new Error(`API request failed (${response.status}).`); return response.json() as Promise<T>; }
const query = (params: Record<string, string | undefined>) => { const search = new URLSearchParams(); Object.entries(params).forEach(([key, value]) => value && search.set(key, value)); return search.toString() ? `?${search}` : ""; };
export const api = {
  seasons: () => request<Envelope<Season[]>>("/api/v1/meta/seasons"),
  status: () => request<Status>("/api/v1/status"),
  teams: (params: Record<string, string | undefined> = {}) => request<Envelope<TeamSummary[]>>(`/api/v1/teams${query(params)}`),
  team: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<TeamDetail>>(`/api/v1/teams/${id}${query(params)}`),
  roster: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<RosterEntry[]>>(`/api/v1/teams/${id}/roster${query(params)}`),
  recentGames: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<RecentGame[]>>(`/api/v1/teams/${id}/recent-games${query(params)}`),
  trends: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<TrendPoint[]>>(`/api/v1/teams/${id}/trends${query(params)}`),
  players: (params: Record<string, string | undefined> = {}) => request<Envelope<PlayerSummary[]>>(`/api/v1/players${query(params)}`),
  player: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<PlayerDetail>>(`/api/v1/players/${id}${query(params)}`),
  playerRecentGames: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<PlayerRecentGame[]>>(`/api/v1/players/${id}/recent-games${query(params)}`),
  playerTrends: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<PlayerTrendPoint[]>>(`/api/v1/players/${id}/trends${query(params)}`),
  playerSplits: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<PlayerSplit[]>>(`/api/v1/players/${id}/splits${query(params)}`),
  explore: (params: Record<string, string | undefined> = {}) => request<Envelope<ExploreData>>(`/api/v1/explore${query(params)}`),
  shotSummary: (params: Record<string, string | undefined> = {}) => request<Envelope<ShotAnalyticsSummary>>(`/api/v1/shots/summary${query(params)}`),
  playerShots: (id: string, params: Record<string, string | undefined> = {}) => request<Envelope<PlayerShotProfile>>(`/api/v1/shots/players/${id}${query(params)}`),
  shotZones: (params: Record<string, string | undefined> = {}) => request<Envelope<ShotDistribution[]>>(`/api/v1/shots/zones${query(params)}`),
  standings: (params: Record<string, string | undefined> = {}) => request<Envelope<StandingsData>>(`/api/v1/standings${query(params)}`),
};
