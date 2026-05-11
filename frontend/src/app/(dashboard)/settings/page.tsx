"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Key, Plus, Trash2, Copy, Check } from "lucide-react";
import api from "@/lib/api";

export default function SettingsPage() {
  const queryClient = useQueryClient();
  const [newKeyName, setNewKeyName] = useState("");
  const [createdKey, setCreatedKey] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const { data: apiKeys = [], isLoading } = useQuery({
    queryKey: ["api-keys"],
    queryFn: async () => {
      const { data } = await api.get("/events/api-keys");
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: () => api.post("/events/api-keys", { name: newKeyName }),
    onSuccess: (res) => {
      setCreatedKey(res.data.raw_key);
      setNewKeyName("");
      queryClient.invalidateQueries({ queryKey: ["api-keys"] });
    },
  });

  const revokeMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/events/api-keys/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["api-keys"] }),
  });

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h1 className="text-xl font-semibold text-gray-900">Settings</h1>
        <p className="text-sm text-gray-500 mt-0.5">Manage API keys for data ingestion</p>
      </div>

      {/* API Keys Section */}
      <div className="bg-white rounded-xl border border-gray-200 p-6">
        <div className="flex items-center gap-2 mb-4">
          <Key size={16} className="text-gray-500" />
          <h2 className="font-medium text-gray-900">API Keys</h2>
        </div>

        {/* Newly created key — show once */}
        {createdKey && (
          <div className="mb-4 bg-green-50 border border-green-200 rounded-lg p-4">
            <p className="text-sm font-medium text-green-800 mb-2">
              ✅ API key created — copy it now, it won't be shown again!
            </p>
            <div className="flex items-center gap-2">
              <code className="flex-1 bg-white border border-green-200 rounded px-3 py-2 text-xs font-mono text-gray-800 break-all">
                {createdKey}
              </code>
              <button
                onClick={() => copyToClipboard(createdKey)}
                className="p-2 text-green-600 hover:bg-green-100 rounded-lg transition-colors"
              >
                {copied ? <Check size={14} /> : <Copy size={14} />}
              </button>
            </div>
            <button
              onClick={() => setCreatedKey(null)}
              className="mt-2 text-xs text-green-600 hover:underline"
            >
              I've saved it, dismiss
            </button>
          </div>
        )}

        {/* Create New Key */}
        <div className="flex gap-2 mb-5">
          <input
            value={newKeyName}
            onChange={(e) => setNewKeyName(e.target.value)}
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
            placeholder="Key name e.g. Production, Mobile App"
          />
          <button
            onClick={() => createMutation.mutate()}
            disabled={!newKeyName.trim() || createMutation.isPending}
            className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={14} />
            {createMutation.isPending ? "Creating..." : "Create"}
          </button>
        </div>

        {/* Key List */}
        {isLoading ? (
          <div className="space-y-2">
            {[...Array(2)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-100 rounded-lg animate-pulse" />
            ))}
          </div>
        ) : apiKeys.length === 0 ? (
          <div className="text-center py-8 text-gray-400 text-sm">
            No API keys yet — create one to start ingesting events
          </div>
        ) : (
          <div className="space-y-2">
            {apiKeys.map((key: any) => (
              <div
                key={key.id}
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="text-sm font-medium text-gray-900">{key.name}</p>
                  <p className="text-xs text-gray-400 font-mono mt-0.5">
                    {key.prefix}••••••••••••
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${
                    key.is_active ? "bg-green-50 text-green-600" : "bg-gray-100 text-gray-500"
                  }`}>
                    {key.is_active ? "active" : "revoked"}
                  </span>
                  <button
                    onClick={() => revokeMutation.mutate(key.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                    title="Revoke key"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}