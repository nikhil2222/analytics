"use client";
import {
  LineChart as RechartsLine,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface Props {
  data: { timestamp: string; count: number }[];
  title: string;
}

export default function LineChart({ data, title }: Props) {
  const formatted = data.map((d) => ({
    ...d,
    time: new Date(d.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
  }));

  return (
    <div className="h-full flex flex-col">
      <p className="text-sm font-medium text-gray-500 mb-3">{title}</p>
      <div className="flex-1">
        <ResponsiveContainer width="100%" height="100%">
          <RechartsLine data={formatted} margin={{ top: 5, right: 10, bottom: 5, left: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} tickLine={false} />
            <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
            <Tooltip
              contentStyle={{ fontSize: 12, borderRadius: 8, border: "1px solid #e5e7eb" }}
            />
            <Line
              type="monotone"
              dataKey="count"
              stroke="#0d9488"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          </RechartsLine>
        </ResponsiveContainer>
      </div>
    </div>
  );
}