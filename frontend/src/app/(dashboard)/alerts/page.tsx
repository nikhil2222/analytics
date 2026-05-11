"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Bell, Plus, Trash2, VolumeX, Volume2, Play } from "lucide-react";
import api from "@/lib/api";
import { Alert } from "@/types";

const STATUS_STYLES: Record<string, string> = {
  active: "bg-green-50 text-green-700",
  triggered: "bg-red-50 text-red-700 animate-pulse",
  resolved: "bg-gray-50 text-gray-600",
  muted: "bg-yellow-50 text-yellow-700",
};

const OPERATORS = [
  { value: "gt", label: ">" },
  { value: "gte", label: ">=" },
  { value: "lt", label: "<" },
  { value: "lte", label: "<=" },
  { value: "eq", label: "=" },
];

export default function AlertsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({
    name: "",
    event_name: "",
    metric: "count",
    operator: "gt",
    threshold: "10",
    time_window_minutes: "10",
    notify_inapp: true,
    notify_webhook: false,
    notify_email: false,
    webhook_url: "",
  });

  const { data: alerts = [], isLoading } = useQuery<Alert[]>({
    queryKey: ["alerts"],
    queryFn: async () => {
      const { data } = await api.get("/alerts/");
      return data;
    },
    refetchInterval: 30_000,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      api.post("/alerts/", {
        ...form,
        threshold: parseFloat(form.threshold),
        time_window_minutes: parseInt(form.time_window_minutes),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["alerts"] });
      setShowCreate(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/alerts/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const muteMutation = useMutation({
    mutationFn: (id: string) => api.post(`/alerts/${id}/mute`, { minutes: 60 }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const unmuteMutation = useMutation({
    mutationFn: (id: string) => api.post(`/alerts/${id}/unmute`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  const evaluateMutation = useMutation({
    mutationFn: (id: string) => api.post(`/alerts/${id}/evaluate`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["alerts"] }),
  });

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Alerts</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {alerts.filter((a) => a.status === "triggered").length} triggered,{" "}
            {alerts.length} total
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} />
          New Alert
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Alert Rule</h2>
            <div className="space-y-3">

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Alert Name</label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  placeholder="e.g. High error rate"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Event Name</label>
                <input
                  value={form.event_name}
                  onChange={(e) => setForm({ ...form, event_name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  placeholder="e.g. error"
                />
              </div>

              {/* Rule — inline */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Rule</label>
                <div className="flex gap-2">
                  <select
                    value={form.metric}
                    onChange={(e) => setForm({ ...form, metric: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  >
                    <option value="count">count</option>
                    <option value="sum">sum</option>
                    <option value="avg">avg</option>
                  </select>
                  <select
                    value={form.operator}
                    onChange={(e) => setForm({ ...form, operator: e.target.value })}
                    className="w-20 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  >
                    {OPERATORS.map((o) => (
                      <option key={o.value} value={o.value}>{o.label}</option>
                    ))}
                  </select>
                  <input
                    type="number"
                    value={form.threshold}
                    onChange={(e) => setForm({ ...form, threshold: e.target.value })}
                    className="w-24 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                    placeholder="100"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Time Window (minutes)
                </label>
                <input
                  type="number"
                  value={form.time_window_minutes}
                  onChange={(e) => setForm({ ...form, time_window_minutes: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  placeholder="10"
                />
              </div>

              {/* Notification channels */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Notify via
                </label>
                <div className="space-y-2">
                  {[
                    { key: "notify_inapp", label: "In-app notification" },
                    { key: "notify_email", label: "Email" },
                    { key: "notify_webhook", label: "Webhook (Slack-compatible)" },
                  ].map(({ key, label }) => (
                    <label key={key} className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={form[key as keyof typeof form] as boolean}
                        onChange={(e) => setForm({ ...form, [key]: e.target.checked })}
                        className="rounded text-teal-600"
                      />
                      {label}
                    </label>
                  ))}
                </div>
              </div>

              {form.notify_webhook && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Webhook URL
                  </label>
                  <input
                    value={form.webhook_url}
                    onChange={(e) => setForm({ ...form, webhook_url: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                    placeholder="https://hooks.slack.com/..."
                  />
                </div>
              )}
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate()}
                disabled={!form.name || !form.event_name || createMutation.isPending}
                className="flex-1 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {createMutation.isPending ? "Creating..." : "Create Alert"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-1/3 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && alerts.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <Bell size={32} className="text-gray-300 mb-3" />
          <p className="text-gray-500 text-sm">No alerts configured</p>
          <p className="text-gray-400 text-xs mt-1 mb-4">
            Create an alert to get notified when metrics cross thresholds
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Create Alert
          </button>
        </div>
      )}

      {/* Alert Cards */}
      {!isLoading && alerts.length > 0 && (
        <div className="space-y-3">
          {alerts.map((alert) => (
            <div
              key={alert.id}
              className="bg-white rounded-xl border border-gray-200 p-5"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <h3 className="font-medium text-gray-900">{alert.name}</h3>
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[alert.status]}`}>
                      {alert.status}
                    </span>
                  </div>

                  {/* Rule description */}
                  <p className="text-sm text-gray-500">
                    When <span className="font-mono bg-gray-100 px-1 rounded text-gray-700">{alert.event_name}</span>{" "}
                    {alert.metric}{" "}
                    <span className="font-bold">{OPERATORS.find(o => o.value === alert.operator)?.label}</span>{" "}
                    <span className="font-bold">{alert.threshold}</span>{" "}
                    in the last <span className="font-medium">{alert.time_window_minutes} min</span>
                  </p>

                  {alert.last_triggered_at && (
                    <p className="text-xs text-gray-400 mt-1">
                      Last triggered: {new Date(alert.last_triggered_at).toLocaleString()}
                    </p>
                  )}

                  {/* History pills */}
                  {alert.history?.length > 0 && (
                    <div className="flex gap-1 mt-2 flex-wrap">
                      {alert.history.slice(0, 5).map((h) => (
                        <span
                          key={h.id}
                          className={`text-xs px-2 py-0.5 rounded-full ${
                            h.status === "triggered"
                              ? "bg-red-50 text-red-500"
                              : "bg-green-50 text-green-600"
                          }`}
                          title={h.message}
                        >
                          {h.status} ({h.triggered_value})
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-1 ml-4">
                  <button
                    onClick={() => evaluateMutation.mutate(alert.id)}
                    title="Evaluate now"
                    className="p-1.5 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                  >
                    <Play size={14} />
                  </button>
                  {alert.status === "muted" ? (
                    <button
                      onClick={() => unmuteMutation.mutate(alert.id)}
                      title="Unmute"
                      className="p-1.5 text-yellow-500 hover:bg-yellow-50 rounded-lg transition-colors"
                    >
                      <Volume2 size={14} />
                    </button>
                  ) : (
                    <button
                      onClick={() => muteMutation.mutate(alert.id)}
                      title="Mute for 1 hour"
                      className="p-1.5 text-gray-400 hover:text-yellow-500 hover:bg-yellow-50 rounded-lg transition-colors"
                    >
                      <VolumeX size={14} />
                    </button>
                  )}
                  <button
                    onClick={() => deleteMutation.mutate(alert.id)}
                    title="Delete"
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}