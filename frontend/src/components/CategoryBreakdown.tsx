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
    <section className="border border-white/8 bg-white/[0.02] p-5">
      <p className="text-[11px] uppercase tracking-[0.32em] text-slate-500">Category Mix</p>
      <h2 className="mt-2 text-2xl text-white">Narrative concentration</h2>
      <div className="mt-6 h-72">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} layout="vertical" margin={{ left: 24 }}>
            <XAxis type="number" hide />
            <YAxis
              dataKey="label"
              type="category"
              tick={{ fill: "#cbd5e1", fontSize: 12 }}
              axisLine={false}
              tickLine={false}
            />
            <Tooltip
              cursor={{ fill: "rgba(255,255,255,0.04)" }}
              contentStyle={{
                backgroundColor: "#07111f",
                border: "1px solid rgba(255,255,255,0.08)",
              }}
            />
            <Bar dataKey="count" fill="#fbbf24" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}

