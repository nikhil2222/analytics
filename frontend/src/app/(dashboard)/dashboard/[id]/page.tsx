"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import { Plus, ArrowLeft, RefreshCw, Share2, Lock } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { Dashboard, Widget } from "@/types";
import WidgetRenderer from "@/components/widgets/WidgetRenderer";

const WIDGET_TYPES = ["line", "bar", "pie", "kpi", "table"];
const TIME_RANGES = ["1h", "24h", "7d", "30d", "90d"];

export default function DashboardDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const [showAddWidget, setShowAddWidget] = useState(false);
  const [sharing, setSharing] = useState(false);

  const [widgetForm, setWidgetForm] = useState({
    title: "",
    type: "line",
    event_name: "",
    time_range: "7d",
    aggregation: "count",
  });

  const { data: dashboard, isLoading } = useQuery<Dashboard>({
    queryKey: ["dashboard", id],
    queryFn: async () => {
      const { data } = await api.get(`/dashboards/${id}`);
      return data;
    },
    enabled: !!id,
  });

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const token = localStorage.getItem("access_token");
    if (!token || !id) return;

    const wsBase =
      process.env.NEXT_PUBLIC_WS_URL?.replace(/^http/, "ws") ||
      "ws://localhost:8000";
    const ws = new WebSocket(`${wsBase}/ws/dashboard/${id}?token=${token}`);

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "new_events") {
        queryClient.invalidateQueries({ queryKey: ["widget-data"] });
      }
    };

    wsRef.current = ws;

    const ping = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ type: "ping" }));
      }
    }, 30_000);

    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [id, queryClient]);

  const addWidgetMutation = useMutation({
    mutationFn: () =>
      api.post(`/dashboards/${id}/widgets`, {
        title: widgetForm.title,
        type: widgetForm.type,
        query_config: {
          event_name: widgetForm.event_name,
          aggregation: widgetForm.aggregation,
          time_range: widgetForm.time_range,
        },
        position: { x: 0, y: 0, w: 4, h: 3 },
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboard", id] });
      setShowAddWidget(false);
      setWidgetForm({
        title: "",
        type: "line",
        event_name: "",
        time_range: "7d",
        aggregation: "count",
      });
    },
  });

  const handleEnablePublicShare = async () => {
    try {
      setSharing(true);
      const { data } = await api.post(`/dashboards/${id}/share/public`);
      const publicUrl = `${window.location.origin}/public-dashboard/${data.public_slug}`;
      await navigator.clipboard.writeText(publicUrl);
      queryClient.invalidateQueries({ queryKey: ["dashboard", id] });
      alert(`Public link copied:\n${publicUrl}`);
    } catch (error: any) {
      alert(
        error?.response?.data?.detail ||
          error?.message ||
          "Failed to enable public sharing"
      );
    } finally {
      setSharing(false);
    }
  };

  const handleDisablePublicShare = async () => {
    try {
      setSharing(true);
      await api.delete(`/dashboards/${id}/share/public`);
      queryClient.invalidateQueries({ queryKey: ["dashboard", id] });
      alert("Public sharing disabled");
    } catch (error: any) {
      alert(
        error?.response?.data?.detail ||
          error?.message ||
          "Failed to disable public sharing"
      );
    } finally {
      setSharing(false);
    }
  };

  const handleCopyExistingPublicLink = async () => {
    try {
      const slug = (dashboard as any)?.public_slug;
      if (!slug) {
        alert("No public link found. Enable public share first.");
        return;
      }
      const publicUrl = `${window.location.origin}/public-dashboard/${slug}`;
      await navigator.clipboard.writeText(publicUrl);
      alert(`Public link copied:\n${publicUrl}`);
    } catch (error: any) {
      alert(error?.message || "Failed to copy public link");
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-24">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    );
  }

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
        <div className="flex items-center gap-3">
          <Link
            href="/dashboard"
            className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft size={18} />
          </Link>

          <div>
            <h1 className="text-xl font-semibold text-gray-900">
              {dashboard?.name}
            </h1>
            {dashboard?.description && (
              <p className="text-sm text-gray-500">{dashboard.description}</p>
            )}

            {(dashboard as any)?.is_public && (
              <p className="text-xs text-green-600 mt-1">
                Public sharing is enabled
              </p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <button
            onClick={() =>
              queryClient.invalidateQueries({ queryKey: ["widget-data"] })
            }
            className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            title="Refresh all widgets"
          >
            <RefreshCw size={16} />
          </button>

          {(dashboard as any)?.is_public ? (
            <>
              <button
                onClick={handleCopyExistingPublicLink}
                disabled={sharing}
                className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                <Share2 size={16} />
                Copy Public Link
              </button>

              <button
                onClick={handleDisablePublicShare}
                disabled={sharing}
                className="flex items-center gap-2 bg-gray-200 hover:bg-gray-300 disabled:opacity-50 text-gray-900 text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                <Lock size={16} />
                {sharing ? "Disabling..." : "Disable Public Share"}
              </button>
            </>
          ) : (
            <button
              onClick={handleEnablePublicShare}
              disabled={sharing}
              className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
            >
              <Share2 size={16} />
              {sharing ? "Enabling..." : "Enable Public Share"}
            </button>
          )}

          <button
            onClick={() => setShowAddWidget(true)}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            Add Widget
          </button>
        </div>
      </div>

      {/* Add Widget Modal */}
      {showAddWidget && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Add Widget
            </h2>

            <div className="space-y-3">
              {[
                {
                  key: "title",
                  label: "Widget Title",
                  type: "text",
                  placeholder: "e.g. Page Views",
                },
                {
                  key: "event_name",
                  label: "Event Name",
                  type: "text",
                  placeholder: "e.g. page_view",
                },
              ].map(({ key, label, type, placeholder }) => (
                <div key={key}>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {label}
                  </label>
                  <input
                    type={type}
                    value={widgetForm[key as keyof typeof widgetForm]}
                    onChange={(e) =>
                      setWidgetForm({
                        ...widgetForm,
                        [key]: e.target.value,
                      })
                    }
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                    placeholder={placeholder}
                  />
                </div>
              ))}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Chart Type
                </label>
                <select
                  value={widgetForm.type}
                  onChange={(e) =>
                    setWidgetForm({ ...widgetForm, type: e.target.value })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                >
                  {WIDGET_TYPES.map((t) => (
                    <option key={t} value={t} className="capitalize">
                      {t}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time Range
                </label>
                <select
                  value={widgetForm.time_range}
                  onChange={(e) =>
                    setWidgetForm({
                      ...widgetForm,
                      time_range: e.target.value,
                    })
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                >
                  {TIME_RANGES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={() => setShowAddWidget(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => addWidgetMutation.mutate()}
                disabled={
                  !widgetForm.title ||
                  !widgetForm.event_name ||
                  addWidgetMutation.isPending
                }
                className="flex-1 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {addWidgetMutation.isPending ? "Adding..." : "Add Widget"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Empty State */}
      {dashboard?.widgets?.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <Plus size={24} className="text-gray-400" />
          </div>
          <h3 className="text-gray-900 font-medium mb-1">No widgets yet</h3>
          <p className="text-gray-500 text-sm mb-4">
            Add your first widget to start visualizing data.
          </p>
          <button
            onClick={() => setShowAddWidget(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Add Widget
          </button>
        </div>
      )}

      {/* Widgets Grid */}
      {dashboard && dashboard.widgets.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {dashboard.widgets.map((widget: Widget) => (
            <WidgetRenderer key={widget.id} widget={widget} dashboardId={id} />
          ))}
        </div>
      )}
    </div>
  );
}