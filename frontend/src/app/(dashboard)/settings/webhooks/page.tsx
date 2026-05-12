"use client";

import { useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Copy, Plus, Trash2, Webhook } from "lucide-react";
import api from "@/lib/api";

type WebhookItem = {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
};

type CreateWebhookResponse = {
  id: string;
  name: string;
  webhook_url: string;
};

export default function WebhooksPage() {
  const queryClient = useQueryClient();
  const [name, setName] = useState("");

  const { data: webhooks = [], isLoading } = useQuery<WebhookItem[]>({
    queryKey: ["webhooks"],
    queryFn: async () => {
      const { data } = await api.get("/events/webhooks");
      return data;
    },
  });

  const createWebhookMutation = useMutation({
    mutationFn: async () => {
      const { data } = await api.post<CreateWebhookResponse>("/events/webhooks", {
        name,
      });
      return data;
    },
    onSuccess: async (data) => {
      await navigator.clipboard.writeText(
        `${window.location.origin.replace(/\/$/, "")}${data.webhook_url}`
      );
      setName("");
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
      alert("Webhook created and URL copied to clipboard");
    },
  });

  const revokeWebhookMutation = useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/events/webhooks/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["webhooks"] });
    },
  });

  const copyWebhookUrl = async (id: string) => {
    const fullUrl = `${process.env.NEXT_PUBLIC_API_URL?.replace(
      /\/api\/v1$/,
      ""
    )}/api/v1/events/ingest/webhook/${id}`;
    await navigator.clipboard.writeText(fullUrl);
    alert("Webhook URL copied");
  };

  const apiBase = useMemo(() => {
    return (process.env.NEXT_PUBLIC_API_URL || "").replace(/\/api\/v1$/, "");
  }, []);

  return (
    <div className="max-w-5xl mx-auto py-8 px-4">
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl bg-teal-50 flex items-center justify-center">
          <Webhook className="text-teal-600" size={20} />
        </div>
        <div>
          <h1 className="text-2xl font-semibold text-gray-900">Webhooks</h1>
          <p className="text-sm text-gray-500">
            Create inbound webhook endpoints to receive external events.
          </p>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-sm mb-6">
        <h2 className="text-base font-semibold text-gray-900 mb-4">
          Create Webhook
        </h2>

        <div className="flex flex-col sm:flex-row gap-3">
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g. Slack Alerts, Shopify Events"
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm text-black focus:outline-none focus:ring-2 focus:ring-teal-500"
          />
          <button
            onClick={() => createWebhookMutation.mutate()}
            disabled={!name.trim() || createWebhookMutation.isPending}
            className="inline-flex items-center justify-center gap-2 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            <Plus size={16} />
            {createWebhookMutation.isPending ? "Creating..." : "Create Webhook"}
          </button>
        </div>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl shadow-sm overflow-hidden">
        <div className="px-5 py-4 border-b border-gray-200">
          <h2 className="text-base font-semibold text-gray-900">
            Existing Webhooks
          </h2>
        </div>

        {isLoading ? (
          <div className="p-6 text-sm text-gray-500">Loading webhooks...</div>
        ) : webhooks.length === 0 ? (
          <div className="p-10 text-center">
            <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
              <Webhook className="text-gray-400" size={22} />
            </div>
            <h3 className="text-sm font-medium text-gray-900 mb-1">
              No webhooks yet
            </h3>
            <p className="text-sm text-gray-500">
              Create your first webhook to start receiving events from external systems.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-gray-200">
            {webhooks.map((webhook) => {
              const fullUrl = `${apiBase}/api/v1/events/ingest/webhook/${webhook.id}`;

              return (
                <div
                  key={webhook.id}
                  className="p-5 flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="text-sm font-semibold text-gray-900">
                        {webhook.name}
                      </p>
                      <span
                        className={`text-[11px] px-2 py-0.5 rounded-full ${
                          webhook.is_active
                            ? "bg-green-50 text-green-700"
                            : "bg-gray-100 text-gray-500"
                        }`}
                      >
                        {webhook.is_active ? "Active" : "Revoked"}
                      </span>
                    </div>

                    <p className="text-xs text-gray-500 mb-2">
                      Created {new Date(webhook.created_at).toLocaleString()}
                    </p>

                    <div className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-xs text-gray-700 break-all">
                      {fullUrl}
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      onClick={() => copyWebhookUrl(webhook.id)}
                      className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <Copy size={15} />
                      Copy URL
                    </button>

                    <button
                      onClick={() => revokeWebhookMutation.mutate(webhook.id)}
                      disabled={
                        revokeWebhookMutation.isPending || !webhook.is_active
                      }
                      className="inline-flex items-center gap-2 px-3 py-2 text-sm border border-red-200 text-red-600 rounded-lg hover:bg-red-50 disabled:opacity-50 transition-colors"
                    >
                      <Trash2 size={15} />
                      Revoke
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}