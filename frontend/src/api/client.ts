import type { Envelope, Season, Status } from "./types";

const base = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
async function request<T>(path: string): Promise<T> { const response = await fetch(`${base}${path}`); if (!response.ok) throw new Error(`API request failed (${response.status}).`); return response.json() as Promise<T>; }
export const api = { seasons: () => request<Envelope<Season[]>>("/api/v1/meta/seasons"), status: () => request<Status>("/api/v1/status") };
