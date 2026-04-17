import { Area, AreaChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import type { TrendItem } from "../types";

type TrendChartProps = {
  trend: TrendItem | null;
};

export function TrendChart({ trend }: TrendChartProps) {
  return (
    <section className="border border-white/8 bg-white/[0.02] p-5">
      <div className="flex items-end justify-between gap-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.32em] text-slate-500">Frequency Curve</p>
          <h2 className="mt-2 text-2xl text-white">{trend ? trend.keyword : "Select a trend"}</h2>
        </div>
        {trend ? (
          <p className="text-sm text-slate-400">
            {trend.status} signal with {trend.recent_count} recent mentions
          </p>
        ) : null}
      </div>

      <div className="mt-6 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={trend?.series ?? []}>
            <defs>
              <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#67e8f9" stopOpacity={0.35} />
                <stop offset="95%" stopColor="#67e8f9" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="rgba(255,255,255,0.08)" vertical={false} />
            <XAxis dataKey="bucket" tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fill: "#94a3b8", fontSize: 12 }} axisLine={false} tickLine={false} />
            <Tooltip
              contentStyle={{
                backgroundColor: "#07111f",
                border: "1px solid rgba(255,255,255,0.08)",
                color: "#fff",
              }}
            />
            <Area
              type="monotone"
              dataKey="count"
              stroke="#67e8f9"
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

