"use client";
import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Activity, Upload, Wifi, WifiOff } from "lucide-react";
import api from "@/lib/api";
import { Event } from "@/types";
import axios from "axios";

export default function EventsPage() {
  const [activeTab, setActiveTab] = useState<"list" | "stream" | "upload">("list");
  const [eventNameFilter, setEventNameFilter] = useState("");
  const [liveEvents, setLiveEvents] = useState<any[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [uploadResult, setUploadResult] = useState<any>(null);
  const [uploading, setUploading] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
const [apiKey, setApiKey] = useState("");
  // ── Event List ──────────────────────────────────────────────────────────
  const { data: events = [], isLoading } = useQuery<Event[]>({
    queryKey: ["events", eventNameFilter],
    queryFn: async () => {
      const params = new URLSearchParams({ limit: "100" });
      if (eventNameFilter) params.set("event_name", eventNameFilter);
      const { data } = await api.get(`/events/?${params}`);
      return data;
    },
  });

  // ── Live Stream WebSocket ───────────────────────────────────────────────
  useEffect(() => {
    if (activeTab !== "stream") {
      wsRef.current?.close();
      setIsConnected(false);
      return;
    }
    const token = localStorage.getItem("access_token");
    if (!token) return;

    const ws = new WebSocket(`ws://localhost:8000/ws/events/stream?token=${token}`);
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => setIsConnected(false);
    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);
      if (msg.type === "new_events") {
        setLiveEvents((prev) => [...msg.events.reverse(), ...prev].slice(0, 200));
      }
    };
    wsRef.current = ws;
    const ping = setInterval(() => ws.send(JSON.stringify({ type: "ping" })), 30_000);
    return () => {
      clearInterval(ping);
      ws.close();
    };
  }, [activeTab]);

  // ── CSV Upload ──────────────────────────────────────────────────────────
const handleCsvUpload = async () => {
  if (!csvFile || !apiKey.trim()) return;
  setUploading(true);
  setUploadResult(null);
  try {
    const formData = new FormData();
    formData.append("file", csvFile);

    const { data } = await axios.post(
      `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"}/events/ingest/csv`,
      formData,
      {
        headers: {
          "X-API-Key": apiKey.trim(),
          "Content-Type": "multipart/form-data",
        },
      }
    );
    setUploadResult(data);
  } catch (e: any) {
    setUploadResult({
      error: e.response?.data?.detail || e.message || "Upload failed",
    });
  } finally {
    setUploading(false);
  }
};

  const tabs = [
    { key: "list", label: "Event List", icon: Activity },
    { key: "stream", label: "Live Stream", icon: Wifi },
    { key: "upload", label: "CSV Upload", icon: Upload },
  ];

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Events</h1>
        <p className="text-sm text-gray-500 mt-0.5">View and stream incoming events</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1 w-fit mb-6">
        {tabs.map(({ key, label, icon: Icon }) => (
          <button
            key={key}
            onClick={() => setActiveTab(key as any)}
            className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-500 hover:text-gray-700"
            }`}
          >
            <Icon size={14} />
            {label}
          </button>
        ))}
      </div>

      {/* ── Event List Tab ── */}
      {activeTab === "list" && (
        <div>
          <div className="mb-4">
            <input
              value={eventNameFilter}
              onChange={(e) => setEventNameFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 w-64"
              placeholder="Filter by event name..."
            />
          </div>

          {isLoading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="bg-white rounded-lg border border-gray-200 p-4 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-1/4 mb-2" />
                  <div className="h-3 bg-gray-100 rounded w-1/3" />
                </div>
              ))}
            </div>
          ) : events.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-24 text-center">
              <Activity size={32} className="text-gray-300 mb-3" />
              <p className="text-gray-500 text-sm">No events found</p>
              <p className="text-gray-400 text-xs mt-1">
                Start ingesting events via the API or CSV upload
              </p>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-gray-100 bg-gray-50">
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Event</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Source</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Properties</th>
                    <th className="text-left px-4 py-3 text-xs font-medium text-gray-500 uppercase tracking-wide">Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {events.map((event) => (
                    <tr key={event.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                      <td className="px-4 py-3 font-medium text-gray-900">{event.name}</td>
                      <td className="px-4 py-3">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${
                          event.source === "api"
                            ? "bg-blue-50 text-blue-600"
                            : event.source === "csv"
                            ? "bg-purple-50 text-purple-600"
                            : "bg-orange-50 text-orange-600"
                        }`}>
                          {event.source}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs font-mono">
                        {event.properties
                          ? JSON.stringify(event.properties).slice(0, 50) + "..."
                          : "—"}
                      </td>
                      <td className="px-4 py-3 text-gray-400 text-xs">
                        {new Date(event.timestamp).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {/* ── Live Stream Tab ── */}
      {activeTab === "stream" && (
        <div>
          <div className="flex items-center gap-2 mb-4">
            <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-gray-300"}`} />
            <span className="text-sm text-gray-600">
              {isConnected ? "Connected — listening for events..." : "Connecting..."}
            </span>
            {liveEvents.length > 0 && (
              <button
                onClick={() => setLiveEvents([])}
                className="ml-auto text-xs text-gray-400 hover:text-gray-600"
              >
                Clear
              </button>
            )}
          </div>

          <div className="bg-gray-950 rounded-xl p-4 font-mono text-xs h-96 overflow-y-auto">
            {liveEvents.length === 0 ? (
              <div className="flex items-center justify-center h-full">
                <p className="text-gray-500">Waiting for events...</p>
              </div>
            ) : (
              <div className="space-y-1">
                {liveEvents.map((e, i) => (
                  <div key={i} className="flex items-start gap-3 text-gray-300">
                    <span className="text-gray-600 shrink-0">
                      {new Date(e.timestamp).toLocaleTimeString()}
                    </span>
                    <span className="text-teal-400">{e.name}</span>
                    <span className="text-gray-500">{e.id?.slice(0, 8)}...</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* ── CSV Upload Tab ── */}
     {activeTab === "upload" && (
  <div className="max-w-lg">
    <div className="bg-white rounded-xl border border-gray-200 p-6">
      <h3 className="font-medium text-gray-900 mb-1">Upload CSV</h3>
      <p className="text-sm text-gray-500 mb-4">
        CSV must have a <code className="bg-gray-100 px-1 rounded">name</code> column.
        Optionally include <code className="bg-gray-100 px-1 rounded">timestamp</code>.
        All other columns become event properties.
      </p>

      {/* Example */}
      <div className="bg-gray-50 rounded-lg p-3 mb-4 font-mono text-xs text-gray-600">
        name,timestamp,country,page<br />
        page_view,2024-01-01T10:00:00,US,/home<br />
        click,2024-01-01T10:01:00,UK,/pricing
      </div>

      {/* API Key input */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          API Key
          <span className="text-gray-400 font-normal ml-1">
            (from Settings — shown once at creation)
          </span>
        </label>
        <input
          type="password"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 font-mono"
          placeholder="ak_xxxxxxxxxxxxxxxx"
        />
      </div>

      {/* File drop zone */}
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
          csvFile
            ? "border-teal-400 bg-teal-50"
            : "border-gray-200 hover:border-teal-400"
        }`}
        onClick={() => document.getElementById("csv-input")?.click()}
      >
        <Upload size={24} className={`mx-auto mb-2 ${csvFile ? "text-teal-500" : "text-gray-400"}`} />
        <p className="text-sm text-gray-500">
          {csvFile ? (
            <span className="text-teal-600 font-medium">{csvFile.name}</span>
          ) : (
            "Click to select a CSV file"
          )}
        </p>
        {csvFile && (
          <p className="text-xs text-gray-400 mt-1">
            {(csvFile.size / 1024).toFixed(1)} KB
          </p>
        )}
        <input
          id="csv-input"
          type="file"
          accept=".csv"
          className="hidden"
          onChange={(e) => {
            setCsvFile(e.target.files?.[0] || null);
            setUploadResult(null);
          }}
        />
      </div>

      {/* Result */}
      {uploadResult && (
        <div className={`mt-3 p-3 rounded-lg text-sm ${
          uploadResult.error
            ? "bg-red-50 text-red-600 border border-red-200"
            : "bg-green-50 text-green-700 border border-green-200"
        }`}>
          {uploadResult.error
            ? `❌ ${uploadResult.error}`
            : `✅ ${uploadResult.ingested} events ingested${
                uploadResult.errors?.length
                  ? ` — ${uploadResult.errors.length} rows skipped`
                  : ""
              }`}
        </div>
      )}

      <button
        onClick={handleCsvUpload}
        disabled={!csvFile || !apiKey.trim() || uploading}
        className="mt-4 w-full bg-teal-600 hover:bg-teal-700 disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-medium py-2.5 rounded-lg transition-colors"
      >
        {uploading ? (
          <span className="flex items-center justify-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white" />
            Uploading...
          </span>
        ) : (
          "Upload & Ingest"
        )}
      </button>
    </div>
  </div>
)}
    </div>
  );
}