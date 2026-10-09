'use client';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import NetworkGraph from '@/components/NetworkGraph';
import MetricCard from '@/components/MetricCard';
import HealingBanner from '@/components/HealingBanner';
import RoutePills from '@/components/RoutePills';
import LogsPanel from '@/components/LogsPanel';
import SecurityPanel from '@/components/SecurityPanel';
import {
  getTopology, findRoute, transmitPacket,
  failLink, failNode, restoreLink, restoreNode, resetNetwork,
} from '@/lib/api';
import type { TopologyState } from '@/lib/types';

const POLL_MS = 2500;

function Legend() {
  return (
    <div style={{
      display: 'flex', flexWrap: 'wrap', gap: '14px 20px',
      padding: '10px 16px', background: '#080c14',
      border: '1px solid #1e2c40', borderRadius: 8, fontSize: '0.75rem', color: '#94a3b8',
    }}>
      {[
        { color: '#10b981', label: 'Online Router' },
        { color: '#f43f5e', label: 'Offline Router' },
        { color: '#00e5ff', label: 'Active Route Node' },
        { color: '#00e5ff', label: '━━ Active Route Link', dashed: false },
        { color: '#f43f5e', label: '┈┈ Severed Link', dashed: true },
        { color: '#334155', label: '━━ Operational Link', dashed: false },
      ].map((item) => (
        <span key={item.label} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{
            display: 'inline-block', width: 10, height: 10, borderRadius: '50%', background: item.color,
            boxShadow: `0 0 6px ${item.color}`,
          }} />
          {item.label}
        </span>
      ))}
    </div>
  );
}

export default function Page() {
  const [topo, setTopo] = useState<TopologyState | null>(null);
  const [activeTab, setActiveTab] = useState<'failure' | 'security' | 'logs'>('failure');
  const [failSubTab, setFailSubTab] = useState<'routing' | 'inject' | 'recover'>('routing');
  const [sourceRouter, setSourceRouter] = useState('A');
  const [destRouter, setDestRouter] = useState('H');
  const [failType, setFailType] = useState<'link' | 'node'>('link');
  const [selLink, setSelLink] = useState('');
  const [selNode, setSelNode] = useState('');
  const [selRestLink, setSelRestLink] = useState('');
  const [selRestNode, setSelRestNode] = useState('');
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [loading, setLoading] = useState(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string, ok: boolean) => {
    setToast({ msg, ok });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3500);
  }, []);

  const update = useCallback((data: TopologyState) => {
    setTopo(data);
    if (data.nodes.length) {
      const ids = data.nodes.map((n) => n.id).sort();
      setSelLink((prev) => {
        const activeLinks = data.links
          .filter((l) => l.status === 'ACTIVE')
          .map((l) => `${l.source}-${l.target}`);
        return activeLinks.includes(prev) ? prev : activeLinks[0] ?? '';
      });
      setSelNode((prev) => {
        const active = data.nodes.filter((n) => n.status === 'ACTIVE').map((n) => n.id);
        return active.includes(prev) ? prev : active[0] ?? '';
      });
      setSelRestLink((prev) => {
        const failed = data.links
          .filter((l) => l.status === 'FAILED')
          .map((l) => `${l.source}-${l.target}`);
        return failed.includes(prev) ? prev : failed[0] ?? '';
      });
      setSelRestNode((prev) => {
        const failed = data.nodes.filter((n) => n.status === 'FAILED').map((n) => n.id);
        return failed.includes(prev) ? prev : failed[0] ?? '';
      });
    }
  }, []);

  // Poll topology
  useEffect(() => {
    let alive = true;
    async function poll() {
      try {
        const data = await getTopology();
        if (alive) update(data);
      } catch { /* backend not ready yet */ }
      if (alive) setTimeout(poll, POLL_MS);
    }
    poll();
    return () => { alive = false; };
  }, [update]);

  async function withLoad<T>(fn: () => Promise<T>, onDone: (r: T) => void) {
    setLoading(true);
    try { onDone(await fn()); }
    catch (e: unknown) { showToast((e as Error).message, false); }
    finally { setLoading(false); }
  }

  if (!topo) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: 16 }}>
        <div style={{ width: 48, height: 48, border: '3px solid #00e5ff', borderTopColor: 'transparent', borderRadius: '50%', animation: 'spin 1s linear infinite' }} />
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>
        <p style={{ color: '#94a3b8' }}>Connecting to MeshGuard backend…</p>
        <p style={{ color: '#475569', fontSize: '0.78rem' }}>Make sure FastAPI is running on port 8000</p>
      </div>
    );
  }

  const allNodeIds = topo.nodes.map((n) => n.id).sort();
  const activeLinks = topo.links.filter((l) => l.status === 'ACTIVE');
  const failedLinks = topo.links.filter((l) => l.status === 'FAILED');
  const activeNodes = topo.nodes.filter((n) => n.status === 'ACTIVE');
  const failedNodes = topo.nodes.filter((n) => n.status === 'FAILED');
  const health = topo.health;
  const pkt = topo.packet_stats;
  const deliveryRate = pkt.packets_sent ? `${Math.round((pkt.packets_delivered / pkt.packets_sent) * 100)}%` : 'N/A';

  const healthTone = health.status.includes('HEALTHY') ? 'green' : health.status.includes('DEGRADED') ? 'amber' : 'red';
  const recTime = topo.last_recovery_time != null ? `${topo.last_recovery_time.toFixed(3)}s` : 'N/A';

  return (
    <div style={{ minHeight: '100vh', background: '#0b0f19' }}>
      {/* Toast */}
      {toast && (
        <div style={{
          position: 'fixed', bottom: 28, right: 28, zIndex: 9999,
          background: toast.ok ? '#10b981' : '#f43f5e',
          color: '#fff', padding: '10px 20px', borderRadius: 10,
          fontWeight: 700, fontSize: '0.85rem', boxShadow: '0 4px 24px rgba(0,0,0,0.5)',
          maxWidth: 360, animation: 'fadeIn 0.2s',
        }}>
          {toast.msg}
        </div>
      )}
      <style>{`@keyframes fadeIn{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}`}</style>

      {/* ── Header ── */}
      <header style={{
        background: 'rgba(11,15,25,0.95)', backdropFilter: 'blur(12px)',
        borderBottom: '1px solid #1e2c40', padding: '14px 32px',
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        position: 'sticky', top: 0, zIndex: 100,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: '1.5rem' }}>🛡️</span>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.1rem', color: '#f8fafc' }}>MeshGuard</div>
            <div style={{ fontSize: '0.72rem', color: '#64748b' }}>Secure Self-Healing Network Simulator</div>
          </div>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <span className={`badge badge-${healthTone}`}>
            <span className="pulse-dot" style={{ background: healthTone === 'green' ? '#10b981' : healthTone === 'amber' ? '#f59e0b' : '#f43f5e' }} />
            {health.status}
          </span>
          <span style={{ fontSize: '0.72rem', color: '#475569' }}>8-Router Mesh · Dijkstra Routing · Next.js</span>
        </div>
      </header>

      <main style={{ maxWidth: 1380, margin: '0 auto', padding: '24px 24px 48px' }}>

        {/* ── Metric Cards ── */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: 14, marginBottom: 24 }}>
          <MetricCard title="Total Clients" value="3 Active" sub="Simulated Endpoints" tone="cyan" icon="💻" />
          <MetricCard title="Active Routers" value={`${topo.stats.active_routers} / ${topo.stats.total_routers}`} sub={`${topo.stats.failed_routers} offline`} tone={topo.stats.failed_routers ? 'red' : 'green'} icon="📶" />
          <MetricCard title="Network Health" value={health.status.split('/')[0].trim()} sub={health.reason} tone={healthTone} icon="📊" />
          <MetricCard title="Packet Reliability" value={deliveryRate} sub={`${pkt.packets_delivered} delivered, ${pkt.packets_lost} lost`} tone={pkt.packets_lost ? 'amber' : 'green'} icon="📦" />
          <MetricCard title="Last Convergence" value={recTime} sub="Self-healing latency" tone="cyan" icon="⚡" />
        </div>

        {/* ── Healing Banner ── */}
        {topo.last_healing_event && <HealingBanner event={topo.last_healing_event} />}

        {/* ── Graph + Legend ── */}
        <div className="panel" style={{ marginBottom: 20, padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '14px 20px', borderBottom: '1px solid #1e2c40', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontWeight: 700, color: '#f8fafc' }}>🌐 Live Network Topology Graph</span>
            <span style={{ fontSize: '0.75rem', color: '#475569' }}>
              {activeNodes.length} nodes online · {activeLinks.length} links active
            </span>
          </div>
          <div style={{ width: '100%', height: 440, background: '#0b0f19' }}>
            <NetworkGraph
              nodes={topo.nodes}
              links={topo.links}
              currentRoute={topo.current_route}
              width={1340}
              height={440}
            />
          </div>
        </div>
        <Legend />

        {/* ── Route Pills ── */}
        {topo.current_route && (
          <RoutePills route={topo.current_route} cost={topo.current_cost} />
        )}

        {/* ── Workspaces ── */}
        <div style={{ marginTop: 28 }}>
          <div style={{ display: 'flex', gap: 8, marginBottom: 20, borderBottom: '1px solid #1e2c40', paddingBottom: 14 }}>
            {([['failure', '⚡ Network Failure Testing'], ['security', '🛡️ Security Testing'], ['logs', '📋 Event Logs']] as const).map(([id, label]) => (
              <button key={id} className={`tab-btn ${activeTab === id ? 'active' : ''}`} onClick={() => setActiveTab(id)}>
                {label}
              </button>
            ))}
          </div>

          {/* FAILURE TESTING TAB */}
          {activeTab === 'failure' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.1fr', gap: 20 }}>
              <div className="panel">
                <div style={{ display: 'flex', gap: 8, marginBottom: 18 }}>
                  {([['routing', 'Routing & Flow'], ['inject', 'Failure Injection'], ['recover', 'Recovery & Reset']] as const).map(([id, label]) => (
                    <button key={id} className={`tab-btn ${failSubTab === id ? 'active' : ''}`} style={{ fontSize: '0.75rem', padding: '6px 12px' }} onClick={() => setFailSubTab(id)}>
                      {label}
                    </button>
                  ))}
                </div>

                {/* Routing & Flow */}
                {failSubTab === 'routing' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label>Source Router</label>
                        <select value={sourceRouter} onChange={(e) => setSourceRouter(e.target.value)}>
                          {allNodeIds.map((id) => <option key={id}>{id}</option>)}
                        </select>
                      </div>
                      <div>
                        <label>Destination Router</label>
                        <select value={destRouter} onChange={(e) => setDestRouter(e.target.value)}>
                          {allNodeIds.map((id) => <option key={id}>{id}</option>)}
                        </select>
                      </div>
                    </div>
                    <button
                      className="btn-primary"
                      disabled={loading}
                      onClick={() => withLoad(
                        () => findRoute(sourceRouter, destRouter),
                        (r) => { update(r.topology ?? r); showToast(`Route found: ${(r.path as string[]).join(' → ')} | Cost: ${r.cost}`, true); }
                      )}
                    >
                      🔍 Find Best Route
                    </button>
                    <button
                      className="btn-primary"
                      disabled={loading || !topo.current_route}
                      onClick={() => withLoad(
                        () => transmitPacket(),
                        (r) => { update(r.topology ?? r); showToast(r.success ? '✅ Packet delivered!' : '❌ Packet dropped!', r.success); }
                      )}
                    >
                      🚀 Transmit Packet
                    </button>
                  </div>
                )}

                {/* Failure Injection */}
                {failSubTab === 'inject' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <button className={`tab-btn ${failType === 'link' ? 'active' : ''}`} style={{ flex: 1 }} onClick={() => setFailType('link')}>Sever Link</button>
                      <button className={`tab-btn ${failType === 'node' ? 'active' : ''}`} style={{ flex: 1 }} onClick={() => setFailType('node')}>Crash Router</button>
                    </div>
                    {failType === 'link' ? (
                      <>
                        <div>
                          <label>Active Link to Sever</label>
                          {activeLinks.length === 0 ? <p style={{ color: '#64748b', fontSize: '0.82rem' }}>All links severed.</p> : (
                            <select value={selLink} onChange={(e) => setSelLink(e.target.value)}>
                              {activeLinks.map((l) => <option key={`${l.source}-${l.target}`} value={`${l.source}-${l.target}`}>{l.source} — {l.target}</option>)}
                            </select>
                          )}
                        </div>
                        <button className="btn-danger" disabled={loading || !selLink} onClick={() => {
                          const [u, v] = selLink.split('-');
                          withLoad(() => failLink(u, v), (r) => { update(r); showToast(`Link ${u}-${v} severed`, false); });
                        }}>💥 Sever Link</button>
                      </>
                    ) : (
                      <>
                        <div>
                          <label>Router to Crash</label>
                          {activeNodes.length === 0 ? <p style={{ color: '#64748b', fontSize: '0.82rem' }}>All routers down.</p> : (
                            <select value={selNode} onChange={(e) => setSelNode(e.target.value)}>
                              {activeNodes.map((n) => <option key={n.id}>{n.id}</option>)}
                            </select>
                          )}
                        </div>
                        <button className="btn-danger" disabled={loading || !selNode} onClick={() => {
                          withLoad(() => failNode(selNode), (r) => { update(r); showToast(`Router ${selNode} crashed`, false); });
                        }}>🛑 Crash Router</button>
                      </>
                    )}
                  </div>
                )}

                {/* Recovery & Reset */}
                {failSubTab === 'recover' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div>
                      <label>Restore Failed Link</label>
                      {failedLinks.length === 0 ? <p style={{ color: '#10b981', fontSize: '0.82rem' }}>✔ All links operational.</p> : (
                        <select value={selRestLink} onChange={(e) => setSelRestLink(e.target.value)}>
                          {failedLinks.map((l) => <option key={`${l.source}-${l.target}`} value={`${l.source}-${l.target}`}>{l.source} — {l.target}</option>)}
                        </select>
                      )}
                    </div>
                    <button className="btn-primary" disabled={loading || !selRestLink} onClick={() => {
                      const [u, v] = selRestLink.split('-');
                      withLoad(() => restoreLink(u, v), (r) => { update(r); showToast(`Link ${u}-${v} restored`, true); });
                    }}>🔄 Restore Link</button>

                    <hr style={{ border: 'none', borderTop: '1px solid #1e2c40', margin: '4px 0' }} />

                    <div>
                      <label>Restore Failed Router</label>
                      {failedNodes.length === 0 ? <p style={{ color: '#10b981', fontSize: '0.82rem' }}>✔ All routers online.</p> : (
                        <select value={selRestNode} onChange={(e) => setSelRestNode(e.target.value)}>
                          {failedNodes.map((n) => <option key={n.id}>{n.id}</option>)}
                        </select>
                      )}
                    </div>
                    <button className="btn-primary" disabled={loading || !selRestNode} onClick={() => {
                      withLoad(() => restoreNode(selRestNode), (r) => { update(r); showToast(`Router ${selRestNode} restored`, true); });
                    }}>🔄 Restore Router</button>

                    <hr style={{ border: 'none', borderTop: '1px solid #1e2c40', margin: '4px 0' }} />

                    <button className="btn-ghost" disabled={loading} onClick={() => {
                      withLoad(() => resetNetwork(), (r) => { update(r); showToast('Network fully reset', true); });
                    }}>♻ Reset Entire Network</button>
                  </div>
                )}
              </div>

              {/* Right: Hop Telemetry + Packet Logs */}
              <div className="panel">
                <div style={{ fontWeight: 700, color: '#f8fafc', marginBottom: 14 }}>📌 Route Breakdown & Hop Telemetry</div>
                {topo.route_hops.length > 0 ? (
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                    <thead>
                      <tr style={{ color: '#64748b', textAlign: 'left', borderBottom: '1px solid #1e2c40' }}>
                        {['Hop', 'From', 'To', 'Cost', 'Total'].map((h) => (
                          <th key={h} style={{ padding: '6px 8px', fontWeight: 600 }}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {topo.route_hops.map((h) => (
                        <tr key={h.hop} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                          <td style={{ padding: '6px 8px', color: '#94a3b8' }}>#{h.hop}</td>
                          <td style={{ padding: '6px 8px', color: '#00e5ff', fontFamily: 'monospace' }}>{h.from}</td>
                          <td style={{ padding: '6px 8px', color: '#00e5ff', fontFamily: 'monospace' }}>{h.to}</td>
                          <td style={{ padding: '6px 8px', color: '#f8fafc' }}>{h.cost}</td>
                          <td style={{ padding: '6px 8px', color: '#10b981' }}>{h.cumulative_cost}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <p style={{ color: '#475569', fontSize: '0.82rem' }}>No active route computed. Use 'Find Best Route' to view telemetry.</p>
                )}

                {topo.packet_logs.length > 0 && (
                  <div style={{ marginTop: 18 }}>
                    <div style={{ fontWeight: 700, color: '#f8fafc', marginBottom: 8, fontSize: '0.88rem' }}>📦 Virtual Packet Telemetry Flow</div>
                    <div style={{
                      background: '#080c14', border: '1px solid #1e2c40', borderRadius: 8,
                      padding: '10px 14px', fontFamily: 'monospace', fontSize: '0.78rem', lineHeight: 1.6,
                    }}>
                      {topo.packet_logs.map((log, i) => (
                        <div key={i} style={{
                          color: log.includes('[OK]') ? '#10b981' : log.includes('[FAIL]') || log.includes('dropped') ? '#f43f5e' : '#38bdf8',
                          fontWeight: log.includes('[OK]') || log.includes('[FAIL]') ? 600 : 400,
                        }}>{log}</div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* SECURITY TAB */}
          {activeTab === 'security' && (
            <SecurityPanel topo={topo} onUpdate={update} />
          )}

          {/* LOGS TAB */}
          {activeTab === 'logs' && <LogsPanel logs={topo.event_logs} />}
        </div>
      </main>

      <footer style={{ textAlign: 'center', padding: '20px 0 32px', borderTop: '1px solid #1e2c40', color: '#334155', fontSize: '0.72rem' }}>
        MESHGUARD · SECURE SELF-HEALING NETWORK SIMULATOR · Next.js + FastAPI Edition
      </footer>
    </div>
  );
}
