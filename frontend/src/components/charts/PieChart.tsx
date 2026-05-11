"use client";
import {
  PieChart as RechartsPie,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const COLORS = ["#0d9488", "#0284c7", "#7c3aed", "#db2777", "#ea580c", "#ca8a04"];

interface Props {
  data: { label: string; value: number }[];
  title: string;
}

export default function PieChart({ data, title }: Props) {
  const formatted = data.map((d) => ({ name: d.label, value: d.value }));

  return (
    <div className="h-full flex flex-col">
      <p className="text-sm font-medium text-gray-500 mb-3">{title}</p>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsPie>
            <Pie
              data={formatted}
              cx="50%"
              cy="50%"
              outerRadius={80}
              dataKey="value"
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
              labelLine={false}
            >
              {formatted.map((_, index) => (
                <Cell key={index} fill={COLORS[index % COLORS.length]} />
              ))}
            </Pie>
            <Tooltip contentStyle={{ fontSize: 12, borderRadius: 8 }} />
          </RechartsPie>
        </ResponsiveContainer>
      </div>
    </div>
  );
}