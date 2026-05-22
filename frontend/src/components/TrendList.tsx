import type { HeadlineRecord, TrendItem } from "../types";

type TrendListProps = {
  trends: TrendItem[];
  headlines: HeadlineRecord[];
  activeKeyword: string | null;
  onSelectKeyword: (keyword: string) => void;
};

export function TrendList({ trends, headlines, activeKeyword, onSelectKeyword }: TrendListProps) {
  return (
    <section className="grid min-w-0 gap-3">
      {trends.map((trend, index) => {
        const related = headlines
          .filter((headline) => trend.related_headlines.includes(headline.id))
          .filter((headline, index, list) => list.findIndex((item) => item.headline === headline.headline) === index);
        const isActive = activeKeyword === trend.keyword;

        return (
          <button
            key={trend.keyword}
            onClick={() => onSelectKeyword(trend.keyword)}
            className={`grid min-w-0 gap-3 overflow-hidden rounded-xl border p-4 text-left shadow-sm transition ${
              isActive
                ? "border-sky-400 bg-sky-50 ring-2 ring-sky-100"
                : "border-slate-200 bg-white hover:border-slate-300 hover:shadow-md"
            }`}
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.3em] text-slate-500">#{index + 1}</p>
                <h3 className="mt-2 text-2xl font-semibold text-slate-900">{trend.keyword}</h3>
              </div>
              <span
                className={`rounded-md px-2 py-1 text-[11px] uppercase tracking-[0.24em] ${
                  trend.status === "emerging"
                    ? "bg-amber-100 text-amber-800"
                    : "bg-emerald-100 text-emerald-800"
                }`}
              >
                {trend.status}
              </span>
            </div>

            <div className="grid grid-cols-3 gap-3 text-sm text-slate-600">
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Recent</p>
                <p className="mt-1 text-lg font-medium text-slate-900">{trend.recent_count}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Baseline</p>
                <p className="mt-1 text-lg font-medium text-slate-900">{trend.baseline_count}</p>
              </div>
              <div>
                <p className="text-[11px] uppercase tracking-[0.22em] text-slate-500">Score</p>
                <p className="mt-1 text-lg font-medium text-slate-900">{trend.score.toFixed(1)}</p>
              </div>
            </div>

            <div className="min-w-0 space-y-1 text-sm text-slate-600">
              {related.slice(0, 2).map((headline) => (
                <p key={headline.id} className="block max-w-full truncate">
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
