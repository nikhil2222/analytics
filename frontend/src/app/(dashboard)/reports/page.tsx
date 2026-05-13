"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  FileText,
  Plus,
  Trash2,
  Play,
  Download,
  ChevronDown,
  ChevronUp,
  Mail,
} from "lucide-react";
import api from "@/lib/api";

type ReportRun = {
  id: string;
  status: "pending" | "running" | "done" | "failed";
  file_path: string | null;
  file_type: string | null;
  error: string | null;
  created_at: string;
  completed_at: string | null;
  emailed: boolean;
};

type Report = {
  id: string;
  name: string;
  dashboard_id: string;
  frequency: string;
  recipients: string[];
  is_active: boolean;
  last_run_at: string | null;
  next_run_at: string | null;
  created_at: string;
  runs: ReportRun[];
};

type Dashboard = {
  id: string;
  name: string;
};

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-yellow-50 text-yellow-700",
  running: "bg-blue-50 text-blue-700 animate-pulse",
  done: "bg-green-50 text-green-700",
  failed: "bg-red-50 text-red-700",
};

const FREQUENCY_LABELS: Record<string, string> = {
  manual: "Manual only",
  daily: "Daily",
  weekly: "Weekly",
  monthly: "Monthly",
};

export default function ReportsPage() {
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [recipientInput, setRecipientInput] = useState("");
  const [form, setForm] = useState({
    name: "",
    dashboard_id: "",
    frequency: "manual",
    recipients: [] as string[],
  });

  const { data: reports = [], isLoading } = useQuery<Report[]>({
    queryKey: ["reports"],
    queryFn: async () => {
      const { data } = await api.get("/reports/");
      return data;
    },
    refetchInterval: 15_000,
  });

  const { data: dashboards = [] } = useQuery<Dashboard[]>({
    queryKey: ["dashboards"],
    queryFn: async () => {
      const { data } = await api.get("/dashboards/");
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/reports/", form),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["reports"] });
      setShowCreate(false);
      setForm({ name: "", dashboard_id: "", frequency: "manual", recipients: [] });
      setRecipientInput("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/reports/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reports"] }),
  });

  const runMutation = useMutation({
    mutationFn: (id: string) => api.post(`/reports/${id}/run`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["reports"] }),
  });

  const addRecipient = () => {
    const email = recipientInput.trim();
    if (email && !form.recipients.includes(email)) {
      setForm({ ...form, recipients: [...form.recipients, email] });
      setRecipientInput("");
    }
  };

  const removeRecipient = (email: string) => {
    setForm({ ...form, recipients: form.recipients.filter((r) => r !== email) });
  };

  const handleDownload = async (reportId: string, runId: string) => {
    const { data } = await api.get(`/reports/${reportId}/runs/${runId}/download`, {
      responseType: "blob",
    });
    const url = window.URL.createObjectURL(new Blob([data]));
    const a = document.createElement("a");
    a.href = url;
    a.download = `report_${runId}.png`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Reports</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {reports.length} report{reports.length !== 1 ? "s" : ""} configured
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} />
          New Report
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6 max-h-[90vh] overflow-y-auto">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Create Report
            </h2>

            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Report Name
                </label>
                <input
                  value={form.name}
                  onChange={(e) => setForm({ ...form, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  placeholder="e.g. Weekly Web Analytics"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Dashboard
                </label>
                <select
                  value={form.dashboard_id}
                  onChange={(e) => setForm({ ...form, dashboard_id: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                >
                  <option value="">Select dashboard...</option>
                  {dashboards.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Frequency
                </label>
                <select
                  value={form.frequency}
                  onChange={(e) => setForm({ ...form, frequency: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                >
                  {Object.entries(FREQUENCY_LABELS).map(([value, label]) => (
                    <option key={value} value={value}>
                      {label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Recipients
                </label>
                <div className="flex gap-2">
                  <input
                    value={recipientInput}
                    onChange={(e) => setRecipientInput(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && addRecipient()}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                    placeholder="user@example.com"
                  />
                  <button
                    type="button"
                    onClick={addRecipient}
                    className="px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm rounded-lg transition-colors"
                  >
                    Add
                  </button>
                </div>

                {form.recipients.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {form.recipients.map((email) => (
                      <span
                        key={email}
                        className="inline-flex items-center gap-1 text-xs bg-teal-50 text-teal-700 px-2 py-1 rounded-full"
                      >
                        {email}
                        <button
                          onClick={() => removeRecipient(email)}
                          className="hover:text-red-500 transition-colors"
                        >
                          ×
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>

            <div className="flex gap-2 mt-5">
              <button
                onClick={() => {
                  setShowCreate(false);
                  setForm({ name: "", dashboard_id: "", frequency: "manual", recipients: [] });
                  setRecipientInput("");
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate()}
                disabled={
                  !form.name || !form.dashboard_id || createMutation.isPending
                }
                className="flex-1 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {createMutation.isPending ? "Creating..." : "Create Report"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Skeleton loading */}
      {isLoading && (
        <div className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <div
              key={i}
              className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse"
            >
              <div className="h-5 bg-gray-200 rounded w-1/3 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && reports.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <FileText size={32} className="text-gray-300 mb-3" />
          <p className="text-gray-500 text-sm">No reports configured</p>
          <p className="text-gray-400 text-xs mt-1 mb-4">
            Create a report to generate PNG snapshots of your dashboards on a schedule
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Create Report
          </button>
        </div>
      )}

      {/* Report cards */}
      {!isLoading && reports.length > 0 && (
        <div className="space-y-3">
          {reports.map((report) => {
            const isExpanded = expandedId === report.id;
            const latestRun = report.runs?.[0];

            return (
              <div
                key={report.id}
                className="bg-white rounded-xl border border-gray-200"
              >
                {/* Card header */}
                <div className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-medium text-gray-900">
                          {report.name}
                        </h3>
                        <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">
                          {FREQUENCY_LABELS[report.frequency]}
                        </span>
                        {latestRun && (
                          <span
                            className={`text-xs px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[latestRun.status]}`}
                          >
                            {latestRun.status}
                          </span>
                        )}
                      </div>

                      <div className="flex flex-wrap gap-3 text-xs text-gray-500 mt-1">
                        {report.last_run_at && (
                          <span>
                            Last run:{" "}
                            {new Date(report.last_run_at).toLocaleString()}
                          </span>
                        )}
                        {report.next_run_at &&
                          report.frequency !== "manual" && (
                            <span>
                              Next:{" "}
                              {new Date(report.next_run_at).toLocaleString()}
                            </span>
                          )}
                        {report.recipients.length > 0 && (
                          <span className="flex items-center gap-1">
                            <Mail size={11} />
                            {report.recipients.length} recipient
                            {report.recipients.length !== 1 ? "s" : ""}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-1 ml-4">
                      <button
                        onClick={() => runMutation.mutate(report.id)}
                        disabled={runMutation.isPending}
                        title="Run now"
                        className="p-1.5 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                      >
                        <Play size={14} />
                      </button>

                      {latestRun?.status === "done" && (
                        <button
                          onClick={() => handleDownload(report.id, latestRun.id)}
                          title="Download latest"
                          className="p-1.5 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg transition-colors"
                        >
                          <Download size={14} />
                        </button>
                      )}

                      <button
                        onClick={() =>
                          setExpandedId(isExpanded ? null : report.id)
                        }
                        title="Run history"
                        className="p-1.5 text-gray-400 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
                      >
                        {isExpanded ? (
                          <ChevronUp size={14} />
                        ) : (
                          <ChevronDown size={14} />
                        )}
                      </button>

                      <button
                        onClick={() => deleteMutation.mutate(report.id)}
                        title="Delete"
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
                  </div>
                </div>

                {/* Run history */}
                {isExpanded && (
                  <div className="border-t border-gray-100 px-5 py-4">
                    <p className="text-xs font-medium text-gray-500 mb-3">
                      Run History
                    </p>

                    {report.runs.length === 0 ? (
                      <p className="text-xs text-gray-400">
                        No runs yet — click ▷ to generate now
                      </p>
                    ) : (
                      <div className="space-y-2">
                        {report.runs.map((run) => (
                          <div
                            key={run.id}
                            className="flex items-center justify-between text-xs"
                          >
                            <div className="flex items-center gap-2">
                              <span
                                className={`px-2 py-0.5 rounded-full font-medium ${STATUS_STYLES[run.status]}`}
                              >
                                {run.status}
                              </span>
                              <span className="text-gray-500">
                                {new Date(run.created_at).toLocaleString()}
                              </span>
                              {run.emailed && (
                                <span className="text-teal-600 flex items-center gap-0.5">
                                  <Mail size={10} /> Sent
                                </span>
                              )}
                              {run.error && (
                                <span
                                  className="text-red-500 truncate max-w-xs"
                                  title={run.error}
                                >
                                  {run.error}
                                </span>
                              )}
                            </div>

                            {run.status === "done" && (
                              <button
                                onClick={() =>
                                  handleDownload(report.id, run.id)
                                }
                                className="flex items-center gap-1 text-blue-600 hover:text-blue-700 transition-colors"
                              >
                                <Download size={12} />
                                Download
                              </button>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}