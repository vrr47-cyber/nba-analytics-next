import type { Envelope, RecentGame, RosterEntry, Season, Status, TeamDetail, TeamSummary, TrendPoint } from "./types";

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
};
