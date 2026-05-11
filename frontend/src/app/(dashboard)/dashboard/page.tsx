"use client";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { Plus, LayoutDashboard, Trash2, ExternalLink } from "lucide-react";
import api from "@/lib/api";
import { Dashboard } from "@/types";

export default function DashboardsPage() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [newName, setNewName] = useState("");
  const [newDesc, setNewDesc] = useState("");

  const { data: dashboards = [], isLoading } = useQuery<Dashboard[]>({
    queryKey: ["dashboards"],
    queryFn: async () => {
      const { data } = await api.get("/dashboards/");
      return data;
    },
  });

  const createMutation = useMutation({
    mutationFn: (payload: { name: string; description: string }) =>
      api.post("/dashboards/", payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["dashboards"] });
      setShowCreate(false);
      setNewName("");
      setNewDesc("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => api.delete(`/dashboards/${id}`),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["dashboards"] }),
  });

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Dashboards</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {dashboards.length} dashboard{dashboards.length !== 1 ? "s" : ""}
          </p>
        </div>
        <button
          onClick={() => setShowCreate(true)}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          <Plus size={16} />
          New Dashboard
        </button>
      </div>

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Create Dashboard</h2>
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Name</label>
                <input
                  value={newName}
                  onChange={(e) => setNewName(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  placeholder="My Dashboard"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Description <span className="text-gray-400">(optional)</span>
                </label>
                <input
                  value={newDesc}
                  onChange={(e) => setNewDesc(e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-teal-500 text-black"
                  placeholder="Brief description..."
                />
              </div>
            </div>
            <div className="flex gap-2 mt-5">
              <button
                onClick={() => setShowCreate(false)}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 text-sm rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => createMutation.mutate({ name: newName, description: newDesc })}
                disabled={!newName.trim() || createMutation.isPending}
                className="flex-1 bg-teal-600 hover:bg-teal-700 disabled:opacity-50 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
              >
                {createMutation.isPending ? "Creating..." : "Create"}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="bg-white rounded-xl border border-gray-200 p-5 animate-pulse">
              <div className="h-5 bg-gray-200 rounded w-2/3 mb-2" />
              <div className="h-4 bg-gray-100 rounded w-1/2" />
            </div>
          ))}
        </div>
      )}

      {/* Empty State */}
      {!isLoading && dashboards.length === 0 && (
        <div className="flex flex-col items-center justify-center py-24 text-center">
          <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
            <LayoutDashboard size={24} className="text-gray-400" />
          </div>
          <h3 className="text-gray-900 font-medium mb-1">No dashboards yet</h3>
          <p className="text-gray-500 text-sm mb-4">
            Create your first dashboard to start visualizing your data.
          </p>
          <button
            onClick={() => setShowCreate(true)}
            className="bg-teal-600 hover:bg-teal-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            Create Dashboard
          </button>
        </div>
      )}

      {/* Dashboard Cards */}
      {!isLoading && dashboards.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dashboards.map((d) => (
            <div
              key={d.id}
              className="bg-white rounded-xl border border-gray-200 p-5 hover:shadow-md transition-shadow group"
            >
              <div className="flex items-start justify-between mb-3">
                <div
                  className="flex-1 cursor-pointer"
                  onClick={() => router.push(`/dashboard/${d.id}`)}
                >
                  <h3 className="font-medium text-gray-900 group-hover:text-teal-600 transition-colors">
                    {d.name}
                  </h3>
                  {d.description && (
                    <p className="text-sm text-gray-500 mt-0.5 line-clamp-1">{d.description}</p>
                  )}
                </div>
                <div className="flex items-center gap-1 ml-2">
                  <button
                    onClick={() => router.push(`/dashboard/${d.id}`)}
                    className="p-1.5 text-gray-400 hover:text-teal-600 hover:bg-teal-50 rounded-lg transition-colors"
                  >
                    <ExternalLink size={14} />
                  </button>
                  <button
                    onClick={() => deleteMutation.mutate(d.id)}
                    className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>
              <div className="flex items-center gap-3 text-xs text-gray-400">
                <span>{d.widgets?.length || 0} widgets</span>
                {d.is_public && (
                  <span className="bg-green-50 text-green-600 px-2 py-0.5 rounded-full">Public</span>
                )}
                {d.refresh_interval && (
                  <span className="bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">
                    Auto-refresh {d.refresh_interval}s
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}