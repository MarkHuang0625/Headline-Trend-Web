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
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <div className="pointer-events-none fixed inset-0 bg-[radial-gradient(circle_at_top_left,_rgba(14,165,233,0.12),_transparent_36%),radial-gradient(circle_at_top_right,_rgba(251,191,36,0.1),_transparent_30%)]" />

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

        <section className="min-w-0 px-5 py-5 sm:px-8 lg:px-10">
          <div className="flex min-w-0 flex-col gap-6">
            <header className="grid gap-4 border-b border-slate-200 pb-6 lg:grid-cols-[1.1fr_0.9fr] lg:items-end">
              <div>
                <p className="text-[11px] uppercase tracking-[0.34em] text-slate-500">Real-Time Trend Map</p>
                <h1 className="mt-3 max-w-2xl font-serif text-4xl leading-tight text-slate-900 sm:text-5xl">
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
                  className="rounded-lg border border-slate-200 bg-white px-4 py-3 text-sm text-slate-900 shadow-sm outline-none placeholder:text-slate-400 focus:border-sky-400 focus:ring-2 focus:ring-sky-100"
                />
                <button
                  onClick={() => setFilters((current) => ({ ...current, search: searchDraft.trim() }))}
                  className="rounded-lg border border-sky-500 bg-sky-500 px-4 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-sky-600"
                >
                  Apply
                </button>
              </div>
            </header>

            <section className="grid gap-4 md:grid-cols-3">
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Window</p>
                <p className="mt-2 text-3xl font-semibold text-slate-900">{filters.windowHours}h</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Tracked Headlines</p>
                <p className="mt-2 text-3xl font-semibold text-slate-900">{data?.tracked_headline_count ?? data?.headlines.length ?? 0}</p>
              </div>
              <div className="rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
                <p className="text-[11px] uppercase tracking-[0.25em] text-slate-500">Top Signal</p>
                <p className="mt-2 text-3xl font-semibold text-slate-900">{data?.trends[0]?.keyword ?? "--"}</p>
              </div>
            </section>

            {error ? (
              <p className="rounded-lg border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700">{error}</p>
            ) : null}
            {loading && !data ? <p className="text-sm text-slate-500">Loading dashboard...</p> : null}

            <div className="grid min-w-0 gap-5 xl:grid-cols-[minmax(0,0.9fr)_minmax(0,1.1fr)]">
              <TrendList
                trends={data?.trends ?? []}
                headlines={data?.headlines ?? []}
                activeKeyword={activeKeyword}
                onSelectKeyword={setActiveKeyword}
              />
              <div className="grid min-w-0 gap-5">
                <TrendChart trend={selectedTrend} />
                <CategoryBreakdown data={data?.category_breakdown ?? []} />
              </div>
            </div>
          </div>
        </section>

        <HeadlineFeed
          headlines={data?.headlines ?? []}
          activeKeyword={activeKeyword}
          relatedHeadlineIds={selectedTrend?.related_headlines}
        />
      </main>
    </div>
  );
}
