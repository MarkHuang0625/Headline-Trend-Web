import { formatCategory, formatRelativeTime } from "../lib/format";
import type { HeadlineRecord } from "../types";

type HeadlineFeedProps = {
  headlines: HeadlineRecord[];
  activeKeyword: string | null;
  relatedHeadlineIds?: number[];
};

const SENTIMENT_STYLES: Record<string, string> = {
  positive: "bg-emerald-100 text-emerald-800",
  negative: "bg-rose-100 text-rose-800",
  neutral: "bg-slate-100 text-slate-700",
};

function matchesTrendKeyword(headline: string, keyword: string): boolean {
  const lower = headline.toLowerCase();
  const tokens = keyword
    .toLowerCase()
    .split(/\s+/)
    .filter((token) => token.length > 3);
  if (!tokens.length) {
    return lower.includes(keyword.toLowerCase());
  }
  return tokens.some((token) => lower.includes(token));
}

export function HeadlineFeed({ headlines, activeKeyword, relatedHeadlineIds = [] }: HeadlineFeedProps) {
  const relatedIds = new Set(relatedHeadlineIds);
  let visible = headlines;

  if (relatedIds.size) {
    visible = headlines.filter((headline) => relatedIds.has(headline.id));
  }

  if (!visible.length && activeKeyword) {
    visible = headlines.filter((headline) => matchesTrendKeyword(headline.headline, activeKeyword));
  }

  return (
    <section className="flex min-h-[720px] flex-col border-l border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 bg-slate-50 px-5 py-5">
        <p className="text-[11px] uppercase tracking-[0.32em] text-slate-500">Live Feed</p>
        <h2 className="mt-2 text-2xl font-semibold text-slate-900">
          {activeKeyword ? `Headlines on ${activeKeyword}` : "Headline tape"}
        </h2>
      </div>
      <div className="flex-1 overflow-y-auto">
        {visible.map((headline) => (
          <article
            key={headline.id}
            className="border-b border-slate-100 px-5 py-4 transition hover:bg-slate-50"
          >
            <div className="flex items-center justify-between gap-4 text-[11px] uppercase tracking-[0.25em] text-slate-500">
              <span>{headline.source}</span>
              <span>{formatRelativeTime(headline.timestamp)}</span>
            </div>
            {headline.url ? (
              <a
                href={headline.url}
                target="_blank"
                rel="noreferrer"
                className="mt-3 block text-sm leading-6 text-slate-800 transition hover:text-sky-700"
              >
                {headline.headline}
              </a>
            ) : (
              <p className="mt-3 text-sm leading-6 text-slate-800">{headline.headline}</p>
            )}
            <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
              <span className="rounded-md bg-slate-100 px-2 py-0.5 text-slate-700">{formatCategory(headline.category)}</span>
              {headline.ticker ? (
                <span className="rounded-md bg-sky-100 px-2 py-0.5 font-medium text-sky-800">{headline.ticker}</span>
              ) : null}
              <span
                className={`rounded-md px-2 py-0.5 capitalize ${SENTIMENT_STYLES[headline.sentiment] ?? SENTIMENT_STYLES.neutral}`}
              >
                {headline.sentiment}
              </span>
            </div>
          </article>
        ))}
        {!visible.length ? (
          <p className="px-5 py-4 text-sm text-slate-500">No matching headlines in this window.</p>
        ) : null}
      </div>
    </section>
  );
}
