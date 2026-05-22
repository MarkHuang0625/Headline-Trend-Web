import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TrendItem } from "../types";

type TrendChartProps = {
  trend: TrendItem | null;
};

export function TrendChart({ trend }: TrendChartProps) {
  return (
    <section className="min-w-0 rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex min-w-0 items-end justify-between gap-4">
        <div className="min-w-0">
          <p className="text-[11px] uppercase tracking-[0.32em] text-slate-500">Frequency Curve</p>
          <h2 className="mt-2 truncate text-2xl font-semibold text-slate-900">{trend ? trend.keyword : "Select a trend"}</h2>
        </div>
        {trend ? (
          <p className="shrink-0 text-sm text-slate-600">
            {trend.status} signal with {trend.recent_count} recent mentions
          </p>
        ) : null}
      </div>

      <div className="mt-6 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={trend?.series ?? []}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#e2e8f0" vertical={false} />
            <XAxis dataKey="bucket" tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#64748b", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                color: "#0f172a",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.08)",
              }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#0284c7"
              fillOpacity={1}
              fill="url(#trendFill)"
              strokeWidth={2}
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
