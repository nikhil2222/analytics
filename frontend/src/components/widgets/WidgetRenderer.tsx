"use client";
import { useQuery } from "@tanstack/react-query";
import { Widget } from "@/types";
import api from "@/lib/api";
import KPICard from "@/components/charts/KPICard";
import LineChart from "@/components/charts/LineChart";
import BarChart from "@/components/charts/BarChart";
import PieChart from "@/components/charts/PieChart";

interface Props {
  widget: Widget;
  dashboardId: string;
}

export default function WidgetRenderer({ widget, dashboardId }: Props) {
  const { data, isLoading, error } = useQuery({
    queryKey: ["widget-data", widget.id],
    queryFn: async () => {
      const { data } = await api.get(
        `/dashboards/${dashboardId}/widgets/${widget.id}/data`
      );
      return data;
    },
    refetchInterval: 60_000, // auto-refresh every 60s
  });

  return (
    <div className="bg-white rounded-xl border border-gray-200 p-5 h-64 flex flex-col">
      {/* Widget Title */}
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold text-gray-800">{widget.title}</h3>
        <span className="text-xs text-gray-400 bg-gray-100 px-2 py-0.5 rounded-full capitalize">
          {widget.type}
        </span>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex-1 flex items-center justify-center">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-teal-600" />
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="flex-1 flex items-center justify-center">
          <p className="text-sm text-red-500">Failed to load data</p>
        </div>
      )}

      {/* Chart */}
      {data && !isLoading && (
        <div className="flex-1 min-h-0">
          {widget.type === "kpi" && (
            <KPICard title={widget.title} value={data.value} label={data.label} />
          )}
          {widget.type === "line" && (
            <LineChart data={data.data || []} title={widget.title} />
          )}
          {widget.type === "bar" && (
            <BarChart data={data.data || []} title={widget.title} />
          )}
          {widget.type === "pie" && (
            <PieChart data={data.data || []} title={widget.title} />
          )}
          {widget.type === "table" && (
            <div className="overflow-auto h-full">
              <table className="w-full text-xs">
                <thead>
                  <tr className="border-b border-gray-100">
                    <th className="text-left py-1.5 text-gray-500 font-medium">Event</th>
                    <th className="text-left py-1.5 text-gray-500 font-medium">Time</th>
                  </tr>
                </thead>
                <tbody>
                  {(data.data || []).map((row: any) => (
                    <tr key={row.id} className="border-b border-gray-50">
                      <td className="py-1.5 text-gray-900">{row.name}</td>
                      <td className="py-1.5 text-gray-400">
                        {new Date(row.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}