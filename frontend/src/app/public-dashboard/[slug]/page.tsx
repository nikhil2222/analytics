"use client";

import { useMemo } from "react";
import { useParams } from "next/navigation";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, RefreshCw, Globe } from "lucide-react";
import Link from "next/link";
import api from "@/lib/api";
import { Dashboard, Widget } from "@/types";
import WidgetRenderer from "@/components/widgets/WidgetRenderer";

export default function PublicDashboardPage() {
  const params = useParams<{ slug: string }>();
  const slug = useMemo(() => {
    const value = params?.slug;
    return Array.isArray(value) ? value[0] : value;
  }, [params]);

  const queryClient = useQueryClient();

  const { data: dashboard, isLoading, isError } = useQuery<Dashboard>({
    queryKey: ["public-dashboard", slug],
    queryFn: async () => {
      const { data } = await api.get(`/dashboards/public/${slug}`);
      return data;
    },
    enabled: !!slug,
    retry: false,
  });

  if (!slug || isLoading) {
    return (
      <div className="flex items-center justify-center py-24 min-h-screen bg-gray-50">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-teal-600" />
      </div>
    );
  }

  if (isError || !dashboard) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-8 text-center max-w-md w-full">
          <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-gray-100 flex items-center justify-center">
            <Globe className="text-gray-400" size={22} />
          </div>
          <h1 className="text-xl font-semibold text-gray-900 mb-2">
            Dashboard not found
          </h1>
          <p className="text-sm text-gray-500">
            This public dashboard may have been removed or sharing may be disabled.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-6 py-6">
        <div className="flex items-center justify-between mb-6 flex-wrap gap-4">
          <div className="flex items-center gap-3">
            <Link
              href="/"
              className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
            >
              <ArrowLeft size={18} />
            </Link>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-xl font-semibold text-gray-900">
                  {dashboard.name}
                </h1>
                <span className="inline-flex items-center gap-1 text-xs text-teal-700 bg-teal-50 px-2 py-1 rounded-full">
                  <Globe size={12} />
                  Public
                </span>
              </div>

              {dashboard.description && (
                <p className="text-sm text-gray-500">{dashboard.description}</p>
              )}
            </div>
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <button
              onClick={() =>
                queryClient.invalidateQueries({
                  queryKey: ["public-dashboard", slug],
                })
              }
              className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              title="Refresh dashboard"
            >
              <RefreshCw size={16} />
            </button>
          </div>
        </div>

        {dashboard.widgets?.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-24 text-center">
            <div className="w-12 h-12 bg-gray-100 rounded-full flex items-center justify-center mb-4">
              <Globe size={24} className="text-gray-400" />
            </div>
            <h3 className="text-gray-900 font-medium mb-1">No widgets yet</h3>
            <p className="text-gray-500 text-sm">
              This public dashboard does not have any widgets yet.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
            {dashboard.widgets.map((widget: Widget) => (
              <WidgetRenderer
                key={widget.id}
                widget={widget}
                dashboardId={dashboard.id}
                // isPublic
                // publicSlug={slug}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}