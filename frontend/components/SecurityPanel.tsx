'use client';
import React from 'react';
import type { ClientState, TopologyState } from '@/lib/types';
import { simulateAttack, securityRequest } from '@/lib/api';

const STATUS_COLORS: Record<string, string> = {
  NORMAL: '#10b981', SUSPICIOUS: '#f59e0b', MALICIOUS: '#f43f5e',
  RECOVERED: '#00e5ff', ISOLATED: '#64748b',
};

interface SecurityResult {
  blocked?: boolean;
  success?: boolean;
  reason?: string;
  topology?: TopologyState;
  [key: string]: unknown;
}

function ClientCard({ client, onUpdate }: { client: ClientState; onUpdate: (t: TopologyState) => void }) {
  const [loading, setLoading] = React.useState<string | null>(null);
  const [msg, setMsg] = React.useState<string | null>(null);

  async function handle(fn: () => Promise<SecurityResult>) {
    setLoading('...');
    setMsg(null);
    try {
      const res = await fn();
      if (res.topology) {
        onUpdate(res.topology);
      }
      if (res.blocked) setMsg('🚫 Route BLOCKED — unauthorized path rejected, safe route restored.');
      else if (res.success) setMsg('✅ Packet delivered to database successfully.');
      else if (res.success === false) setMsg('❌ Delivery failed.');
    } catch (e: unknown) {
      setMsg(`Error: ${(e as Error).message}`);
    } finally { setLoading(null); }
  }

  const color = STATUS_COLORS[client.status] ?? '#94a3b8';
  return (
    <div style={{
      background: '#080c14', border: `1px solid ${color}33`,
      borderRadius: 10, padding: '14px 16px', marginBottom: 12,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <strong style={{ color: '#f8fafc' }}>{client.client_id}</strong>
        <span className={`badge`} style={{
          background: `${color}18`, border: `1px solid ${color}55`, color,
        }}>
          <span className="pulse-dot" style={{ background: color, width: 7, height: 7 }} />
          {client.status}
        </span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 6, fontSize: '0.78rem', color: '#94a3b8', marginBottom: 10 }}>
        <span>Trust: <strong style={{ color }}>{client.trust_score}/100</strong></span>
        <span>Delivered: <strong style={{ color: '#10b981' }}>{client.delivered}</strong></span>
        <span>Blocked: <strong style={{ color: '#f43f5e' }}>{client.blocked_requests}</strong></span>
        <span>Changes: <strong style={{ color: '#f59e0b' }}>{client.route_changes}</strong></span>
      </div>
      {client.route && (
        <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 8, fontFamily: 'monospace' }}>
          Route: {client.route.join(' → ')}
        </div>
      )}
      {client.last_request && (
        <div style={{ fontSize: '0.72rem', color: '#64748b', marginBottom: 10 }}>Last: {client.last_request}</div>
      )}
      {msg && (
        <div style={{ fontSize: '0.78rem', color: msg.startsWith('✅') ? '#10b981' : msg.startsWith('🚫') ? '#f59e0b' : '#f43f5e', marginBottom: 8, padding: '6px 10px', background: 'rgba(255,255,255,0.04)', borderRadius: 6 }}>
          {msg}
        </div>
      )}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
        <button
          className="btn-primary"
          disabled={!!loading}
          onClick={() => handle(() => securityRequest(client.client_id))}
        >
          {loading === 'req' ? '⏳' : '📡'} Request DB
        </button>
        <button
          className="btn-danger"
          disabled={!!loading}
          onClick={() => handle(() => simulateAttack(client.client_id))}
        >
          {loading === 'atk' ? '⏳' : '💀'} Simulate Attack
        </button>
      </div>
    </div>
  );
}

export default function SecurityPanel({ topo, onUpdate }: { topo: TopologyState; onUpdate: (t: TopologyState) => void }) {
  const clients = Object.values(topo.clients);
  return (
    <div>
      <div style={{ fontSize: '0.83rem', color: '#94a3b8', marginBottom: 16 }}>
        Simulate malicious clients proposing unauthorized routes. The Request Gate validates each route before any packet is forwarded.
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: 12 }}>
        {clients.map((c) => (
          <ClientCard key={c.client_id} client={c} onUpdate={(t) => onUpdate(t)} />
        ))}
      </div>
    </div>
  );
}
