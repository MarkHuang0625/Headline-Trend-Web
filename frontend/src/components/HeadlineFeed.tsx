import { formatCategory, formatRelativeTime } from "../lib/format";
import type { HeadlineRecord } from "../types";

type HeadlineFeedProps = {
  headlines: HeadlineRecord[];
  activeKeyword: string | null;
};

export function HeadlineFeed({ headlines, activeKeyword }: HeadlineFeedProps) {
  const visible = activeKeyword
    ? headlines.filter((headline) => headline.headline.toLowerCase().includes(activeKeyword.toLowerCase()))
    : headlines;

  return (
    <section className="flex min-h-[720px] flex-col border-l border-white/10 bg-[#060c16]/90">
      <div className="border-b border-white/8 px-5 py-5">
        <p className="text-[11px] uppercase tracking-[0.32em] text-slate-500">Live Feed</p>
        <h2 className="mt-2 text-2xl text-white">{activeKeyword ? `Headlines on ${activeKeyword}` : "Headline tape"}</h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {visible.map((headline) => (
          <article
            key={headline.id}
            className="border-b border-white/8 px-5 py-4 transition hover:bg-white/[0.02]"
          >
            <div className="flex items-center justify-between gap-4 text-[11px] uppercase tracking-[0.25em] text-slate-500">
              <span>{headline.source}</span>
              <span>{formatRelativeTime(headline.timestamp)}</span>
            </div>
            <p className="mt-3 text-sm leading-6 text-slate-100">{headline.headline}</p>
            <div className="mt-3 flex flex-wrap gap-2 text-xs text-slate-400">
              <span>{formatCategory(headline.category)}</span>
              {headline.ticker ? <span>{headline.ticker}</span> : null}
              <span className="capitalize">{headline.sentiment}</span>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

