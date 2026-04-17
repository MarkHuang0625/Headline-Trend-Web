export type HeadlineRecord = {
  id: number;
  headline: string;
  source: string;
  timestamp: string;
  category: string;
  ticker: string | null;
  sentiment: "positive" | "negative" | "neutral";
  tags: string[];
};

export type TrendPoint = {
  bucket: string;
  count: number;
};

export type TrendItem = {
  keyword: string;
  recent_count: number;
  baseline_count: number;
  score: number;
  status: "emerging" | "persistent";
  related_headlines: number[];
  series: TrendPoint[];
};

export type CategoryBreakdownItem = {
  category: string;
  count: number;
};

export type DashboardResponse = {
  generated_at: string;
  window_hours: number;
  trends: TrendItem[];
  category_breakdown: CategoryBreakdownItem[];
  headlines: HeadlineRecord[];
  available_tickers: string[];
};

