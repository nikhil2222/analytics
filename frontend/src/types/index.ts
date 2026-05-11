export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: "owner" | "admin" | "analyst" | "viewer";
  org_id: string;
}

export interface Dashboard {
  id: string;
  name: string;
  description: string | null;
  is_public: boolean;
  public_slug: string | null;
  refresh_interval: number | null;
  widgets: Widget[];
  created_at: string;
  created_by: string;
}

export interface Widget {
  id: string;
  title: string;
  type: "line" | "bar" | "pie" | "kpi" | "table";
  query_config: QueryConfig;
  position: { x: number; y: number; w: number; h: number };
  dashboard_id: string;
  created_at: string;
}

export interface QueryConfig {
  event_name: string;
  aggregation: string;
  time_range: string;
  group_by?: string;
  filters?: Record<string, unknown>;
}

export interface Alert {
  id: string;
  name: string;
  event_name: string;
  metric: string;
  operator: string;
  threshold: number;
  status: "active" | "triggered" | "resolved" | "muted";
  time_window_minutes: number;
  last_triggered_at: string | null;
  history: AlertHistory[];
  created_at: string;
}

export interface AlertHistory {
  id: string;
  status: string;
  triggered_value: number;
  threshold: number;
  message: string;
  created_at: string;
}

export interface Event {
  id: string;
  name: string;
  source: string;
  timestamp: string;
  properties: Record<string, unknown> | null;
  org_id: string;
}