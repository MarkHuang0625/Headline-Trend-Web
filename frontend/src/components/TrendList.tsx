import type { HeadlineRecord, TrendItem } from "../types";

type TrendListProps = {
  trends: TrendItem[];
  headlines: HeadlineRecord[];
  activeKeyword: string | null;
  onSelectKeyword: (keyword: string) => void;
};

export function TrendList({ trends, headlines, activeKeyword, onSelectKeyword }: TrendListProps) {
  return (
    <section className="grid gap-3">
      {trends.map((trend, index) => {
        const related = headlines.filter((headline) => trend.related_headlines.includes(headline.id));
        const isActive = activeKeyword === trend.keyword;

        return (
          <button
            key={trend.keyword}
            onClick={() => onSelectKeyword(trend.keyword)}
            className={`grid gap-3 border p-4 text-left transition ${
              isActive
                ? "border-cyan-300 bg-cyan-300/8"
                : "border-white/8 bg-white/[0.02] hover:border-white/20"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">#{index + 1}</p>
                <h3 className="mt-2 text-2xl font-semibold text-white">{trend.keyword}</h3>
              </div>
              <span
                className={`px-2 py-1 text-[11px] uppercase tracking-[0.24em] ${
                  trend.status === "emerging" ? "text-amber-200" : "text-emerald-200"
                }`}
              >
                {trend.status}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm text-slate-400">
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Recent</p>
                <p className="mt-1 text-lg text-white">{trend.recent_count}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Baseline</p>
                <p className="mt-1 text-lg text-white">{trend.baseline_count}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Score</p>
                <p className="mt-1 text-lg text-white">{trend.score.toFixed(1)}</p>
              </div>
            </div>

            <div className="space-y-1 text-sm text-slate-400">
              {related.slice(0, 2).map((headline) => (
                <p key={headline.id} className="truncate">
                  {headline.headline}
                </p>
              ))}
            </div>
          </button>
        );
      })}
    </section>
  );
}

