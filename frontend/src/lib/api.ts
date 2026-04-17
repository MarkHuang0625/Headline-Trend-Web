import type { DashboardResponse } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export type DashboardFilters = {
  search: string;
  category: string;
  ticker: string;
  windowHours: number;
};

export async function fetchDashboard(filters: DashboardFilters): Promise<DashboardResponse> {
  const params = new URLSearchParams();
  if (filters.search) params.set("search", filters.search);
  if (filters.category) params.set("category", filters.category);
  if (filters.ticker) params.set("ticker", filters.ticker);
  params.set("window_hours", String(filters.windowHours));

  const response = await fetch(`${API_BASE_URL}/api/dashboard?${params.toString()}`);
  if (!response.ok) {
    throw new Error("Failed to load dashboard");
  }
  return response.json() as Promise<DashboardResponse>;
}

