import { formatCategory } from "../lib/format";

type SidebarProps = {
  categories: string[];
  activeCategory: string;
  onSelectCategory: (category: string) => void;
  tickers: string[];
  activeTicker: string;
  onSelectTicker: (ticker: string) => void;
  windowHours: number;
  onWindowHoursChange: (hours: number) => void;
};

const WINDOWS = [1, 6, 24];

export function Sidebar({
  categories,
  activeCategory,
  onSelectCategory,
  tickers,
  activeTicker,
  onSelectTicker,
  windowHours,
  onWindowHoursChange,
}: SidebarProps) {
  return (
    <aside className="flex min-h-[720px] flex-col justify-between border-r border-white/10 bg-[#07111f]/90 p-6">
      <div className="space-y-8">
        <div className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.35em] text-cyan-300/80">Market Pulse</p>
          <h1 className="max-w-[10rem] font-serif text-3xl leading-none text-white">
            Headline trend terminal
          </h1>
          <p className="max-w-[12rem] text-sm leading-6 text-slate-400">
            Watch macro, sector, stock, and geopolitical narratives form in real time.
          </p>
        </div>

        <section className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Categories</p>
          <div className="space-y-2">
            {categories.map((category) => (
              <button
                key={category}
                onClick={() => onSelectCategory(category)}
                className={`flex w-full items-center justify-between border px-3 py-2 text-left text-sm transition ${
                  activeCategory === category
                    ? "border-cyan-300 bg-cyan-400/10 text-cyan-100"
                    : "border-white/8 text-slate-400 hover:border-white/20 hover:text-white"
                }`}
              >
                <span>{formatCategory(category)}</span>
                <span className="text-xs text-slate-500">{category === "all" ? "ALL" : "LIVE"}</span>
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Window</p>
          <div className="flex gap-2">
            {WINDOWS.map((hours) => (
              <button
                key={hours}
                onClick={() => onWindowHoursChange(hours)}
                className={`flex-1 border px-3 py-2 text-sm transition ${
                  windowHours === hours
                    ? "border-amber-300 bg-amber-400/10 text-amber-100"
                    : "border-white/8 text-slate-400 hover:border-white/20 hover:text-white"
                }`}
              >
                {hours}h
              </button>
            ))}
          </div>
        </section>

        <section className="space-y-3">
          <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">Watchlist</p>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => onSelectTicker("")}
              className={`border px-3 py-1.5 text-xs transition ${
                !activeTicker
                  ? "border-cyan-300 text-cyan-100"
                  : "border-white/8 text-slate-400 hover:border-white/20 hover:text-white"
              }`}
            >
              All
            </button>
            {tickers.map((ticker) => (
              <button
                key={ticker}
                onClick={() => onSelectTicker(ticker)}
                className={`border px-3 py-1.5 text-xs transition ${
                  activeTicker === ticker
                    ? "border-cyan-300 text-cyan-100"
                    : "border-white/8 text-slate-400 hover:border-white/20 hover:text-white"
                }`}
              >
                {ticker}
              </button>
            ))}
          </div>
        </section>
      </div>

      <div className="border-t border-white/10 pt-5 text-xs leading-5 text-slate-500">
        Emerging trends are detected from frequency spikes in the most recent slice of the selected window.
      </div>
    </aside>
  );
}

