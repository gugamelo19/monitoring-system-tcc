export type DashboardSummary = {
  assets: {
    total: number;
    online: number;
    offline: number;
    unstable: number;
    unknown?: number;
  };
  events: {
    total: number;
  };
  anomalies: {
    total: number;
  };
  alerts: {
    open: number;
    in_progress: number;
    resolved: number;
    false_positive?: number;
  };
};

export type ProtocolItem = {
  protocol: string;
  total: number;
};

export type SeverityItem = {
  severity: string;
  total: number;
};

export type RecentEvent = {
  id: string;
  asset: string;
  asset_name: string;
  source_ip: string;
  destination_ip: string;
  source_port?: number | null;
  destination_port?: number | null;
  protocol: string;
  transport_layer?: string | null;
  packet_size?: number | null;
  tcp_flags?: string | null;
  dns_query?: string | null;
  icmp_type?: number | null;
  icmp_code?: number | null;
  event_timestamp: string;
  raw_summary?: string | null;
  collector_name?: string | null;
};

export type RecentAlert = {
  id: string;
  anomaly: string;
  anomaly_type: string;
  asset_name: string;
  title: string;
  message: string;
  severity: string;
  status: string;
  created_at: string;
};
