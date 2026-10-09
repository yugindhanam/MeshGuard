'use client';
import React, { useState } from 'react';
import type { ClientState, TopologyState } from '@/lib/types';
import { simulateAttack, securityRequest } from '@/lib/api';

const STATUS_CONFIG: Record<
  string,
  { color: string; bg: string; border: string; icon: string; label: string }
> = {
  NORMAL: { color: '#10b981', bg: 'rgba(16, 185, 129, 0.12)', border: 'rgba(16, 185, 129, 0.35)', icon: '✔', label: 'NORMAL' },
  SUSPICIOUS: { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.35)', icon: '⚠️', label: 'SUSPICIOUS' },
  MALICIOUS: { color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.15)', border: 'rgba(244, 63, 94, 0.4)', icon: '✖', label: 'MALICIOUS' },
  RECOVERED: { color: '#00e5ff', bg: 'rgba(0, 229, 255, 0.12)', border: 'rgba(0, 229, 255, 0.35)', icon: '⚡', label: 'RECOVERED' },
  ISOLATED: { color: '#64748b', bg: 'rgba(100, 116, 139, 0.12)', border: 'rgba(100, 116, 139, 0.35)', icon: '🔒', label: 'ISOLATED' },
};

interface SecurityResult {
  blocked?: boolean;
  success?: boolean;
  reason?: string;
  topology?: TopologyState;
  [key: string]: unknown;
}

export default function SecurityPanel({
  topo,
  onUpdate,
}: {
  topo: TopologyState;
  onUpdate: (t: TopologyState) => void;
}) {
  const clients = Object.values(topo.clients);
  const [selectedClientId, setSelectedClientId] = useState<string>('Client 2');
  const [loadingClient, setLoadingClient] = useState<string | null>(null);
  const [bannerMsg, setBannerMsg] = useState<{ text: string; ok: boolean } | null>(null);

  const selectedClient = topo.clients[selectedClientId] || clients[0];

  async function handleAction(clientId: string, actionFn: () => Promise<SecurityResult>) {
    setLoadingClient(clientId);
    setBannerMsg(null);
    try {
      const res = await actionFn();
      if (res.topology) {
        onUpdate(res.topology);
      }
      if (res.blocked) {
        setBannerMsg({
          text: `🚫 [${clientId}] Unauthorized route blocked! Re-routed via Dijkstra safe path.`,
          ok: false,
        });
      } else if (res.success) {
        setBannerMsg({
          text: `✅ [${clientId}] Valid request forwarded and delivered to Database (Router H).`,
          ok: true,
        });
      } else {
        setBannerMsg({
          text: `❌ [${clientId}] Request delivery failed. No active path to Database.`,
          ok: false,
        });
      }
    } catch (e: unknown) {
      setBannerMsg({
        text: `Error: ${(e as Error).message}`,
        ok: false,
      });
    } finally {
      setLoadingClient(null);
    }
  }

  const incident = selectedClient?.last_incident;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      {/* Educational Banner */}
      <div
        style={{
          background: '#0c1424',
          border: '1px solid #1e3a5f',
          borderRadius: 10,
          padding: '14px 18px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div>
          <strong style={{ color: '#00e5ff', fontSize: '0.88rem', display: 'flex', alignItems: 'center', gap: 6 }}>
            <span>🛡️ Simulated Client Request Gate & Policy Enforcement</span>
          </strong>
          <p style={{ margin: '4px 0 0 0', color: '#94a3b8', fontSize: '0.78rem', lineHeight: 1.5 }}>
            Simulates endpoint clients sending requests to the shared Database at Router H.
            MeshGuard pre-validates all proposed routes against the active topology before forwarding packets.
          </p>
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span
            style={{
              fontSize: '0.72rem',
              color: '#10b981',
              background: 'rgba(16, 185, 129, 0.1)',
              padding: '4px 10px',
              borderRadius: 6,
              border: '1px solid rgba(16, 185, 129, 0.3)',
            }}
          >
            ✔ Isolation Verified: Honest clients remain unaffected
          </span>
        </div>
      </div>

      {bannerMsg && (
        <div
          style={{
            padding: '10px 16px',
            borderRadius: 8,
            fontSize: '0.82rem',
            fontWeight: 600,
            background: bannerMsg.ok ? 'rgba(16, 185, 129, 0.15)' : 'rgba(244, 63, 94, 0.15)',
            border: `1px solid ${bannerMsg.ok ? '#10b981' : '#f43f5e'}`,
            color: bannerMsg.ok ? '#10b981' : '#f43f5e',
          }}
        >
          {bannerMsg.text}
        </div>
      )}

      {/* 3 Simulated Clients Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 14 }}>
        {clients.map((client) => {
          const cfg = STATUS_CONFIG[client.status] || STATUS_CONFIG.NORMAL;
          const isSelected = client.client_id === selectedClientId;
          const isLoading = loadingClient === client.client_id;
          const score = Math.max(0, Math.min(100, client.trust_score));
          const scoreColor = score >= 80 ? '#10b981' : score >= 50 ? '#f59e0b' : '#f43f5e';

          return (
            <div
              key={client.client_id}
              onClick={() => setSelectedClientId(client.client_id)}
              style={{
                background: '#080c14',
                border: `2px solid ${isSelected ? '#00e5ff' : 'rgba(30, 44, 64, 0.8)'}`,
                borderRadius: 12,
                padding: '16px 18px',
                cursor: 'pointer',
                transition: 'all 0.2s',
                boxShadow: isSelected ? '0 0 16px rgba(0, 229, 255, 0.15)' : 'none',
              }}
            >
              {/* Card Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div>
                  <strong style={{ fontSize: '0.98rem', color: '#f8fafc' }}>{client.client_id}</strong>
                  <div style={{ fontSize: '0.72rem', color: '#64748b' }}>
                    Source: Router {client.source} → DB (Router {client.destination})
                  </div>
                </div>
                <span
                  style={{
                    background: cfg.bg,
                    border: `1px solid ${cfg.border}`,
                    color: cfg.color,
                    padding: '3px 8px',
                    borderRadius: 6,
                    fontSize: '0.72rem',
                    fontWeight: 800,
                    display: 'flex',
                    alignItems: 'center',
                    gap: 4,
                  }}
                >
                  <span>{cfg.icon}</span>
                  <span>{cfg.label}</span>
                </span>
              </div>

              {/* Trust Score Meter */}
              <div style={{ marginBottom: 14 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.74rem', marginBottom: 4 }}>
                  <span style={{ color: '#94a3b8' }}>Client Trust Score:</span>
                  <strong style={{ color: scoreColor, fontFamily: 'monospace' }}>{score} / 100</strong>
                </div>
                <div
                  style={{
                    width: '100%',
                    height: 6,
                    background: '#1e2c40',
                    borderRadius: 4,
                    overflow: 'hidden',
                  }}
                  role="progressbar"
                  aria-valuenow={score}
                  aria-valuemin={0}
                  aria-valuemax={100}
                >
                  <div
                    style={{
                      width: `${score}%`,
                      height: '100%',
                      background: scoreColor,
                      transition: 'width 0.4s ease',
                    }}
                  />
                </div>
              </div>

              {/* Telemetry Stats */}
              <div
                style={{
                  display: 'grid',
                  gridTemplateColumns: '1fr 1fr',
                  gap: 8,
                  fontSize: '0.75rem',
                  color: '#94a3b8',
                  background: 'rgba(255, 255, 255, 0.02)',
                  padding: '8px 10px',
                  borderRadius: 6,
                  marginBottom: 12,
                }}
              >
                <div>Delivered: <strong style={{ color: '#10b981' }}>{client.delivered}</strong></div>
                <div>Blocked: <strong style={{ color: client.blocked_requests > 0 ? '#f43f5e' : '#94a3b8' }}>{client.blocked_requests}</strong></div>
                <div>Route Shifts: <strong style={{ color: '#f59e0b' }}>{client.route_changes}</strong></div>
                <div>Last Status: <strong style={{ color: '#e2e8f0', fontSize: '0.7rem' }}>{client.last_request || 'Idle'}</strong></div>
              </div>

              {/* Active Route */}
              <div style={{ fontSize: '0.72rem', marginBottom: 14 }}>
                <span style={{ color: '#64748b' }}>Current Path: </span>
                <code style={{ color: '#00e5ff', fontFamily: 'monospace' }}>
                  {client.route ? client.route.join(' → ') : 'None (Isolated)'}
                </code>
              </div>

              {/* Action Buttons */}
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <button
                  className="btn-primary"
                  style={{ fontSize: '0.78rem', padding: '7px 10px' }}
                  disabled={isLoading}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAction(client.client_id, () => securityRequest(client.client_id));
                  }}
                >
                  {isLoading ? '⏳ Working...' : '📡 Send Request'}
                </button>
                <button
                  className="btn-danger"
                  style={{ fontSize: '0.78rem', padding: '7px 10px' }}
                  disabled={isLoading}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleAction(client.client_id, () => simulateAttack(client.client_id));
                  }}
                >
                  {isLoading ? '⏳ Working...' : '💀 Simulate Attack'}
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Incident Lifecycle & Guided Walkthrough */}
      <div
        className="panel"
        style={{
          border: '1px solid #1e3a5f',
          background: '#090e1a',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: '#00e5ff', fontWeight: 700, letterSpacing: '0.08em' }}>
              SECURITY INCIDENT LIFECYCLE AUDIT
            </div>
            <h4 style={{ fontSize: '1.05rem', fontWeight: 800, color: '#f8fafc', margin: '4px 0 0 0' }}>
              Real-Time Route Validation Lifecycle: {selectedClient.client_id}
            </h4>
          </div>
          <span
            style={{
              padding: '4px 10px',
              borderRadius: 6,
              fontSize: '0.75rem',
              fontWeight: 800,
              backgroundColor: incident ? 'rgba(244, 63, 94, 0.15)' : 'rgba(16, 185, 129, 0.15)',
              border: `1px solid ${incident ? '#f43f5e' : '#10b981'}`,
              color: incident ? '#f43f5e' : '#10b981',
            }}
          >
            {incident ? '⚠️ INCIDENT REGISTERED' : '✔ NO INCIDENTS PENDING'}
          </span>
        </div>

        {/* 5-Stage Incident Flow Pipeline */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 8, marginBottom: 20 }}>
          {[
            {
              num: '01',
              title: 'Detection',
              desc: incident ? 'Abnormal route intercepted' : 'Continuous monitoring',
              active: !!incident,
              failed: false,
            },
            {
              num: '02',
              title: 'Validation',
              desc: incident ? 'Policy rules checked' : 'Pre-flight route gate',
              active: !!incident,
              failed: false,
            },
            {
              num: '03',
              title: 'Blocking',
              desc: incident ? 'Rogue hops dropped (0 sent)' : 'Enforces valid edges',
              active: !!incident,
              failed: true,
            },
            {
              num: '04',
              title: 'Recalculation',
              desc: incident ? 'Dijkstra on trusted nodes' : 'Self-healing ready',
              active: !!incident,
              failed: false,
            },
            {
              num: '05',
              title: 'Recovery',
              desc: incident?.safe_path ? 'Safe verified delivery' : 'Normal state',
              active: !!incident,
              failed: false,
            },
          ].map((st) => (
            <div
              key={st.num}
              style={{
                background: '#060a12',
                border: `1px solid ${st.active ? (st.failed ? '#f43f5e' : '#00e5ff') : '#1e2c40'}`,
                borderRadius: 8,
                padding: '10px 12px',
              }}
            >
              <div
                style={{
                  fontSize: '0.68rem',
                  fontFamily: 'monospace',
                  color: st.active ? (st.failed ? '#f43f5e' : '#00e5ff') : '#64748b',
                  fontWeight: 700,
                  marginBottom: 2,
                }}
              >
                STAGE {st.num}
              </div>
              <strong style={{ fontSize: '0.8rem', color: '#f8fafc', display: 'block' }}>{st.title}</strong>
              <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginTop: 2 }}>{st.desc}</div>
            </div>
          ))}
        </div>

        {/* Path Comparison Cards (When Incident Occurs) */}
        {incident ? (
          <div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
              {/* Baseline */}
              <div style={{ background: '#080c14', padding: 12, borderRadius: 8, border: '1px solid #1e2c40' }}>
                <div style={{ fontSize: '0.7rem', color: '#94a3b8', fontWeight: 700, textTransform: 'uppercase' }}>
                  ① Baseline Trusted Path
                </div>
                <div style={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: '0.8rem', marginTop: 6 }}>
                  {incident.previous_path?.join(' → ') || 'A → B → D → F → H'}
                </div>
              </div>

              {/* Blocked Rogue Proposal */}
              <div style={{ background: '#180a0f', padding: 12, borderRadius: 8, border: '1px solid #f43f5e' }}>
                <div style={{ fontSize: '0.7rem', color: '#f43f5e', fontWeight: 700, textTransform: 'uppercase' }}>
                  ② Blocked Rogue Proposal (Rejected)
                </div>
                <div style={{ color: '#fda4af', fontFamily: 'monospace', fontSize: '0.8rem', marginTop: 6 }}>
                  {incident.invalid_path?.join(' → ') || 'A → Unauthorized X → H'}
                </div>
              </div>

              {/* Recovered Safe Route */}
              <div style={{ background: '#06161c', padding: 12, borderRadius: 8, border: '1px solid #00e5ff' }}>
                <div style={{ fontSize: '0.7rem', color: '#00e5ff', fontWeight: 700, textTransform: 'uppercase' }}>
                  ③ Recovered Safe Route (Dijkstra)
                </div>
                <div style={{ color: '#38bdf8', fontFamily: 'monospace', fontSize: '0.8rem', marginTop: 6 }}>
                  {incident.safe_path?.join(' → ') || 'A → B → D → F → H'}
                </div>
              </div>
            </div>

            {/* Incident Audit Details */}
            <div
              style={{
                background: '#080c14',
                border: '1px solid #1e2c40',
                borderRadius: 8,
                padding: '12px 16px',
                fontSize: '0.78rem',
              }}
            >
              <div style={{ fontWeight: 700, color: '#f43f5e', marginBottom: 6 }}>
                🔍 Security Audit Reasons for Rejection:
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, color: '#cbd5e1', lineHeight: 1.6 }}>
                {incident.reasons?.map((r, i) => (
                  <li key={i}>{r}</li>
                )) || <li>Unauthorized node injected into routing proposal</li>}
              </ul>
              <div style={{ marginTop: 8, color: '#10b981', fontWeight: 600 }}>
                ✓ Outcome: Unauthorized proposal blocked with 0 packets transmitted. Safe Dijkstra path re-established and verified.
              </div>
            </div>
          </div>
        ) : (
          <div
            style={{
              background: '#080c14',
              border: '1px solid #1e2c40',
              borderRadius: 8,
              padding: '14px 18px',
              color: '#94a3b8',
              fontSize: '0.8rem',
              lineHeight: 1.6,
            }}
          >
            <div>✔ No active security violations recorded for <strong>{selectedClient.client_id}</strong>.</div>
            <div style={{ color: '#64748b', fontSize: '0.74rem', marginTop: 4 }}>
              Click <strong>&quot;Simulate Attack&quot;</strong> above on any client to inject an invalid proposal and watch
              real-time detection, policy rejection, and safe path self-healing.
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
