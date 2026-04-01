"use client";

import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { SeverityItem } from "@/types/dashboard";

type Props = {
  data: SeverityItem[];
};

const COLORS = ["#38bdf8", "#facc15", "#fb923c", "#f87171"];

export function SeverityChart({ data }: Props) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-900 p-5">
      <h2 className="mb-4 text-lg font-semibold text-white">Alertas por severidade</h2>
      <div className="h-80">
        <ResponsiveContainer width="100%" height="100%">
          <PieChart>
            <Pie data={data} dataKey="total" nameKey="severity" outerRadius={110} label>
              {data.map((entry, index) => (
                <Cell key={entry.severity} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip />
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}