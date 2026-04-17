import { useEffect, useState } from "react";

import { CategoryBreakdown } from "./components/CategoryBreakdown";
import { HeadlineFeed } from "./components/HeadlineFeed";
import { Sidebar } from "./components/Sidebar";
import { TrendChart } from "./components/TrendChart";
import { TrendList } from "./components/TrendList";
import { fetchDashboard, type DashboardFilters } from "./lib/api";
import type { DashboardResponse } from "./types";

const DEFAULT_FILTERS: DashboardFilters = {
  search: "",
  category: "all",
  ticker: "",
  windowHours: 24,
};

export default function App() {
  const [filters, setFilters] = useState<DashboardFilters>(DEFAULT_FILTERS);
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [activeKeyword, setActiveKeyword] = useState<string | null>(null);
  const [searchDraft, setSearchDraft] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setSearchDraft(filters.search);
  }, [filters.search]);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        const next = await fetchDashboard(filters);
        if (!cancelled) {
          setData(next);
          setActiveKeyword((current) =>
            current && next.trends.some((trend) => trend.keyword === current)
              ? current
              : next.trends[0]?.keyword ?? null
          );
          setError(null);
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(loadError instanceof Error ? loadError.message : "Unknown error");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }

    load();
    const interval = window.setInterval(load, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [filters]);

  const selectedTrend = data?.trends.find((trend) => trend.keyword === activeKeyword) ?? null;
  const categories = ["all", "macro", "single_stock", "sector", "geopolitics"];

  return (
    <div className="min-h-screen bg-[#02050b] text-white">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(103,232,249,0.14),_transparent_32%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.12),_transparent_26%),linear-gradient(180deg,_rgba(255,255,255,0.02),_transparent_30%)]" />

      <main className="relative grid min-h-screen lg:grid-cols-[260px_minmax(0,1fr)_360px]">
        <Sidebar
          categories={categories}
          activeCategory={filters.category}
          onSelectCategory={(category) => setFilters((current) => ({ ...current, category }))}
          tickers={data?.available_tickers ?? []}
          activeTicker={filters.ticker}
          onSelectTicker={(ticker) => setFilters((current) => ({ ...current, ticker }))}
          windowHours={filters.windowHours}
          onWindowHoursChange={(windowHours) => setFilters((current) => ({ ...current, windowHours }))}
        />

        <section className="px-5 py-5 sm:px-8 lg:px-10">
          <div className="flex flex-col gap-6">
            <header className="grid gap-4 border-b border-white/8 pb-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
              <div>
                <p className="text-[11px] uppercase tracking-[0.34em] text-slate-500">Real-Time Trend Map</p>
                <h1 className="mt-3 max-w-2xl font-serif text-4xl leading-tight text-white sm:text-5xl">
                  Separate the noise from the narrative.
                </h1>
              </div>
              <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
                <input
                  value={searchDraft}
                  onChange={(event) => setSearchDraft(event.target.value)}
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      setFilters((current) => ({ ...current, search: searchDraft.trim() }));
                    }
                  }}
                  placeholder="Search keyword or company"
                  className="border border-white/10 bg-white/[0.03] px-4 py-3 text-sm text-white outline-none placeholder:text-slate-500 focus:border-cyan-300"
                />
                <button
                  onClick={() => setFilters((current) => ({ ...current, search: searchDraft.trim() }))}
                  className="border border-cyan-300/60 px-4 py-3 text-sm text-cyan-100 transition hover:bg-cyan-300/10"
                >
                  Apply
                </button>
              </div>
            </header>

            <section className="grid gap-4 md:grid-cols-3">
              <div className="border border-white/8 bg-white/[0.02] p-4">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Window</p>
                <p className="mt-2 text-3xl text-white">{filters.windowHours}h</p>
              </div>
              <div className="border border-white/8 bg-white/[0.02] p-4">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Tracked Headlines</p>
                <p className="mt-2 text-3xl text-white">{data?.headlines.length ?? 0}</p>
              </div>
              <div className="border border-white/8 bg-white/[0.02] p-4">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Top Signal</p>
                <p className="mt-2 text-3xl text-white">{data?.trends[0]?.keyword ?? "--"}</p>
              </div>
            </section>

            {error ? <p className="border border-rose-400/30 bg-rose-400/10 p-4 text-sm text-rose-100">{error}</p> : null}
            {loading && !data ? <p className="text-sm text-slate-400">Loading dashboard...</p> : null}

            <div className="grid gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <TrendList
                trends={data?.trends ?? []}
                headlines={data?.headlines ?? []}
                activeKeyword={activeKeyword}
                onSelectKeyword={setActiveKeyword}
              />
              <div className="grid gap-5">
                <TrendChart trend={selectedTrend} />
                <CategoryBreakdown data={data?.category_breakdown ?? []} />
              </div>
            </div>
          </div>
        </section>

        <HeadlineFeed headlines={data?.headlines ?? []} activeKeyword={activeKeyword} />
      </main>
    </div>
  );
}

