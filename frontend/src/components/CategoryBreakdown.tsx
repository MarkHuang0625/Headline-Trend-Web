import { Bar, BarChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { formatCategory } from "../lib/format";
import type { CategoryBreakdownItem } from "../types";

type CategoryBreakdownProps = {
  data: CategoryBreakdownItem[];
};

export function CategoryBreakdown({ data }: CategoryBreakdownProps) {
  const chartData = data.map((item) => ({
    ...item,
    label: formatCategory(item.category),
  }));

  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <p className="text-[11px] uppercase tracking-[0.32em] text-slate-500">Category Mix</p>
      <h2 className="mt-2 text-2xl font-semibold text-slate-900">Narrative concentration</h2>
      <div className="mt-6 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
            <XAxis type="number" hide />
            <YAxis
              dataKey="label"
              type="category"
              tick={{ fill: "#475569", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: "rgba(14, 165, 233, 0.08)" }}
              contentStyle={{
                backgroundColor: "#ffffff",
                border: "1px solid #e2e8f0",
                borderRadius: "8px",
                color: "#0f172a",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.08)",
              }}
            />
            <Bar dataKey="count" fill="#f59e0b" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
