export interface NodeData {
  id: string;
  label: string;
  x: number;
  y: number;
  status: 'ACTIVE' | 'FAILED';
}

export interface LinkData {
  source: string;
  target: string;
  weight: number;
  status: 'ACTIVE' | 'FAILED';
}

export interface NetStats {
  total_routers: number;
  active_routers: number;
  failed_routers: number;
  total_links: number;
  active_links: number;
  failed_links: number;
}

export interface HealthInfo {
  status: string;
  badge: string;
  is_reachable: boolean;
  reason: string;
  failed_nodes: string[];
  failed_links: [string, string][];
}

export interface HopDetail {
  hop: number;
  from: string;
  to: string;
  link: string;
  cost: number;
  cumulative_cost: number;
}

export interface HealingEvent {
  failure_type: string;
  failed_item: string;
  status: 'RECOVERED' | 'FAILED_NO_PATH' | 'UNAFFECTED';
  original_path: string[] | null;
  recovered_path: string[] | null;
  recovered_cost: number | null;
  recovery_time: number;
  message: string;
}

export interface IncidentData {
  previous_path?: string[];
  invalid_path?: string[];
  classification?: string;
  reasons?: string[];
  blocked?: boolean;
  safe_path?: string[] | null;
  delivered?: boolean;
}

export interface ClientState {
  client_id: string;
  source: string;
  destination: string;
  route: string[] | null;
  status: string;
  trust_score: number;
  route_changes: number;
  blocked_requests: number;
  delivered: number;
  last_request: string;
  last_incident: IncidentData | null;
  expected_route: string[] | null;
}

export interface LogEntry {
  timestamp: string;
  message: string;
}

export interface TopologyState {
  nodes: NodeData[];
  links: LinkData[];
  stats: NetStats;
  packet_stats: { packets_sent: number; packets_delivered: number; packets_lost: number };
  health: HealthInfo;
  current_route: string[] | null;
  current_cost: number | null;
  route_hops: HopDetail[];
  last_healing_event: HealingEvent | null;
  last_recovery_time: number | null;
  packet_logs: string[];
  source_router: string;
  dest_router: string;
  clients: Record<string, ClientState>;
  event_logs: LogEntry[];
}
