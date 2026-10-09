'use client';
import React, { useCallback, useEffect, useRef, useState } from 'react';
import NetworkGraph from '@/components/NetworkGraph';
import MetricCard from '@/components/MetricCard';
import HealingBanner from '@/components/HealingBanner';
import RoutePills from '@/components/RoutePills';
import LogsPanel from '@/components/LogsPanel';
import SecurityPanel from '@/components/SecurityPanel';
import VivaGuide from '@/components/VivaGuide';
import TerminologyModal from '@/components/TerminologyModal';
import {
  getTopology,
  findRoute,
  transmitPacket,
  failLink,
  failNode,
  restoreLink,
  restoreNode,
  resetNetwork,
} from '@/lib/api';
import type { TopologyState } from '@/lib/types';

const POLL_INTERVAL_MS = 2500;

function AccessibleLegend() {
  const items = [
    { icon: '●', color: '#10b981', label: 'Online Router', pattern: 'Solid emerald circle' },
    { icon: '✖', color: '#f43f5e', label: 'Offline / Down Router', pattern: 'Pulsing crimson circle' },
    { icon: '★', color: '#00e5ff', label: 'Active Route Router', pattern: 'Glowing cyan node' },
    { icon: '🗄️', color: '#a855f7', label: 'Database Node (H)', pattern: 'Purple target node' },
    { icon: '━━', color: '#00e5ff', label: 'Active Route Link', pattern: 'Thick glowing cyan line' },
    { icon: '┈┈', color: '#f43f5e', label: 'Severed / Failed Link', pattern: 'Dashed red laser' },
    { icon: '━━', color: '#334155', label: 'Operational Link', pattern: 'Slate link with cost badge' },
  ];

  return (
    <div
      style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '12px 18px',
        padding: '12px 18px',
        background: '#080c14',
        border: '1px solid #1e2c40',
        borderRadius: 8,
        fontSize: '0.74rem',
        color: '#94a3b8',
        marginTop: 10,
      }}
    >
      <div style={{ fontWeight: 700, color: '#e2e8f0', marginRight: 4 }}>
        Topology Legend:
      </div>
      {items.map((item) => (
        <span
          key={item.label}
          style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          title={item.pattern}
        >
          <span
            style={{
              color: item.color,
              fontFamily: 'monospace',
              fontWeight: 800,
              fontSize: '0.85rem',
            }}
          >
            {item.icon}
          </span>
          <span>{item.label}</span>
        </span>
      ))}
    </div>
  );
}

export default function MeshGuardDashboard() {
  const [topo, setTopo] = useState<TopologyState | null>(null);
  const [connectionError, setConnectionError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'failure' | 'security' | 'logs'>('failure');
  const [failSubTab, setFailSubTab] = useState<'routing' | 'inject' | 'recover'>('routing');
  const [sourceRouter, setSourceRouter] = useState<string>('A');
  const [destRouter, setDestRouter] = useState<string>('H');
  const [failType, setFailType] = useState<'link' | 'node'>('link');
  const [selLink, setSelLink] = useState<string>('');
  const [selNode, setSelNode] = useState<string>('');
  const [selRestLink, setSelRestLink] = useState<string>('');
  const [selRestNode, setSelRestNode] = useState<string>('');
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [isActionLoading, setIsActionLoading] = useState<boolean>(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const showToast = useCallback((msg: string, ok: boolean) => {
    setToast({ msg, ok });
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToast(null), 3800);
  }, []);

  const updateTopologyState = useCallback((data: TopologyState) => {
    setTopo(data);
    setConnectionError(null);
    if (data.nodes && data.nodes.length > 0) {
      setSelLink((prev) => {
        const activeLinks = data.links
          .filter((l) => l.status === 'ACTIVE')
          .map((l) => `${l.source}-${l.target}`);
        return activeLinks.includes(prev) ? prev : activeLinks[0] ?? '';
      });
      setSelNode((prev) => {
        const activeNodes = data.nodes.filter((n) => n.status === 'ACTIVE').map((n) => n.id);
        return activeNodes.includes(prev) ? prev : activeNodes[0] ?? '';
      });
      setSelRestLink((prev) => {
        const failedLinks = data.links
          .filter((l) => l.status === 'FAILED')
          .map((l) => `${l.source}-${l.target}`);
        return failedLinks.includes(prev) ? prev : failedLinks[0] ?? '';
      });
      setSelRestNode((prev) => {
        const failedNodes = data.nodes.filter((n) => n.status === 'FAILED').map((n) => n.id);
        return failedNodes.includes(prev) ? prev : failedNodes[0] ?? '';
      });
    }
  }, []);

  // Poll topology from FastAPI
  useEffect(() => {
    let isMounted = true;
    async function fetchState() {
      try {
        const data = await getTopology();
        if (isMounted) updateTopologyState(data);
      } catch (err: unknown) {
        if (isMounted && !topo) {
          setConnectionError((err as Error).message || 'Unable to connect to backend server');
        }
      }
      if (isMounted) setTimeout(fetchState, POLL_INTERVAL_MS);
    }
    fetchState();
    return () => {
      isMounted = false;
    };
  }, [updateTopologyState, topo]);

  async function executeAction<T>(actionFn: () => Promise<T>, onSuccess: (result: T) => void) {
    setIsActionLoading(true);
    try {
      const res = await actionFn();
      onSuccess(res);
    } catch (err: unknown) {
      showToast((err as Error).message, false);
    } finally {
      setIsActionLoading(false);
    }
  }

  // Offline / Error screen
  if (!topo) {
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          gap: 20,
          background: '#0b0f19',
          color: '#f8fafc',
          padding: 24,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            width: 56,
            height: 56,
            border: '3px solid #00e5ff',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
        <style>{`@keyframes spin{to{transform:rotate(360deg)}}`}</style>

        <div>
          <h2 style={{ fontSize: '1.4rem', fontWeight: 800, margin: '0 0 6px 0' }}>
            Connecting to MeshGuard Backend
          </h2>
          <p style={{ color: '#94a3b8', fontSize: '0.88rem', margin: '0 0 12px 0' }}>
            Awaiting response from FastAPI telemetry server at <code>http://localhost:8000</code>
          </p>

          {connectionError && (
            <div
              style={{
                maxWidth: 480,
                background: 'rgba(244, 63, 94, 0.1)',
                border: '1px solid rgba(244, 63, 94, 0.4)',
                borderRadius: 8,
                padding: '12px 16px',
                color: '#f87171',
                fontSize: '0.8rem',
                marginBottom: 16,
              }}
            >
              <strong>Connection Warning:</strong> {connectionError}
              <div style={{ marginTop: 8, color: '#cbd5e1', fontSize: '0.74rem' }}>
                Tip: Run <code>start-backend.bat</code> or <code>python -m uvicorn backend.server:app --port 8000</code> in your terminal.
              </div>
            </div>
          )}

          <button
            className="btn-primary"
            style={{ width: 'auto', padding: '10px 24px' }}
            onClick={() => {
              getTopology()
                .then(updateTopologyState)
                .catch((e) => showToast(`Retry failed: ${e.message}`, false));
            }}
          >
            🔄 Retry Connection
          </button>
        </div>
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
  const deliveryRate = pkt.packets_sent
    ? `${Math.round((pkt.packets_delivered / pkt.packets_sent) * 100)}%`
    : '100%';

  const healthTone = health.status.includes('HEALTHY')
    ? 'green'
    : health.status.includes('DEGRADED')
    ? 'amber'
    : 'red';

  const recoveryTimeStr =
    topo.last_recovery_time !== null && topo.last_recovery_time !== undefined
      ? `${topo.last_recovery_time.toFixed(3)}s`
      : 'No failure active';

  const isSourceDown = !activeNodes.some((n) => n.id === sourceRouter);
  const isDestDown = !activeNodes.some((n) => n.id === destRouter);

  return (
    <div style={{ minHeight: '100vh', background: '#0b0f19', color: '#f8fafc' }}>
      {/* Toast Notification */}
      {toast && (
        <div
          role="status"
          aria-live="polite"
          style={{
            position: 'fixed',
            bottom: 24,
            right: 24,
            zIndex: 9999,
            background: toast.ok ? '#064e3b' : '#881337',
            border: `1px solid ${toast.ok ? '#10b981' : '#f43f5e'}`,
            color: '#fff',
            padding: '12px 20px',
            borderRadius: 10,
            fontWeight: 700,
            fontSize: '0.85rem',
            boxShadow: '0 8px 30px rgba(0,0,0,0.6)',
            maxWidth: 380,
            display: 'flex',
            alignItems: 'center',
            gap: 10,
          }}
        >
          <span>{toast.ok ? '✔' : '✖'}</span>
          <span>{toast.msg}</span>
        </div>
      )}

      {/* ── NOC Masthead Header ── */}
      <header
        style={{
          background: 'rgba(11, 15, 25, 0.96)',
          backdropFilter: 'blur(12px)',
          borderBottom: '1px solid #1e2c40',
          padding: '12px 28px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          position: 'sticky',
          top: 0,
          zIndex: 100,
          flexWrap: 'wrap',
          gap: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ fontSize: '1.6rem' }}>🛡️</span>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 800, fontSize: '1.15rem', color: '#f8fafc' }}>MeshGuard</span>
              <span
                style={{
                  fontSize: '0.68rem',
                  fontFamily: 'monospace',
                  background: 'rgba(0, 229, 255, 0.1)',
                  color: '#00e5ff',
                  padding: '2px 6px',
                  borderRadius: 4,
                  border: '1px solid rgba(0, 229, 255, 0.25)',
                }}
              >
                NOC v2.0
              </span>
            </div>
            <div style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
              Secure Self-Healing Computer Network Simulator · Dynamic Dijkstra Routing & Policy Enforcement
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          {/* Health Pill */}
          <span
            className={`badge badge-${healthTone}`}
            title={`Status: ${health.status} (${health.reason})`}
          >
            <span
              className="pulse-dot"
              style={{
                background:
                  healthTone === 'green' ? '#10b981' : healthTone === 'amber' ? '#f59e0b' : '#f43f5e',
              }}
            />
            {health.status}
          </span>

          {/* Terminology Guide Button */}
          <TerminologyModal />

          {/* Quick Reset Button */}
          <button
            className="tab-btn"
            style={{ fontSize: '0.75rem', padding: '6px 12px' }}
            onClick={() => {
              executeAction(resetNetwork, (r) => {
                updateTopologyState(r);
                showToast('Network topology reset to clean healthy state', true);
              });
            }}
            title="Reset all routers and links to clean operational state"
          >
            ♻ Reset Network
          </button>
        </div>
      </header>

      {/* ── Main Workspace Container ── */}
      <main style={{ maxWidth: 1400, margin: '0 auto', padding: '20px 24px 60px' }}>
        {/* Viva & Demonstration Guide Accordion */}
        <VivaGuide />

        {/* ── Executive Overview Metrics (5 Key Cards) ── */}
        <section aria-label="Network Telemetry Overview" style={{ marginBottom: 20 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(5, 1fr)',
              gap: 12,
            }}
          >
            <MetricCard
              title="Network Health"
              value={health.status.split('/')[0].trim()}
              sub={health.reason}
              tone={healthTone}
              icon="📊"
              badge={health.is_reachable ? 'REACHABLE' : 'PARTITIONED'}
              tooltip="Evaluates end-to-end reachability across the active subgraph"
            />
            <MetricCard
              title="Router Status"
              value={`${topo.stats.active_routers} / ${topo.stats.total_routers} Online`}
              sub={`${topo.stats.failed_routers} Offline Nodes`}
              tone={topo.stats.failed_routers > 0 ? 'red' : 'green'}
              icon="📶"
              badge={`${topo.stats.active_routers} UP`}
              tooltip="Current count of operational vs crashed routers in the topology"
            />
            <MetricCard
              title="Mesh Link Adjacency"
              value={`${topo.stats.active_links} / ${topo.stats.total_links} Active`}
              sub={`${topo.stats.failed_links} Severed Links`}
              tone={topo.stats.failed_links > 0 ? 'amber' : 'green'}
              icon="🔗"
              badge={`${topo.stats.active_links} HEALTHY`}
              tooltip="Operational bidirectional connections between routers"
            />
            <MetricCard
              title="Virtual Packet Delivery"
              value={deliveryRate}
              sub={`${pkt.packets_delivered} delivered, ${pkt.packets_lost} lost`}
              tone={pkt.packets_lost > 0 ? 'amber' : 'green'}
              icon="📦"
              badge={`${pkt.packets_sent} SENT`}
              tooltip="Packet delivery reliability metric from the simulation engine"
            />
            <MetricCard
              title="Simulated Convergence"
              value={recoveryTimeStr}
              sub="Dijkstra Recalculation Time"
              tone="cyan"
              icon="⚡"
              badge="LATENCY"
              tooltip="Simulated elapsed wall-clock duration for failure detection and route recalculation"
            />
          </div>
        </section>

        {/* ── Self-Healing Incident Notification ── */}
        {topo.last_healing_event && <HealingBanner event={topo.last_healing_event} />}

        {/* ── Topology Visualizer Canvas ── */}
        <section aria-label="Network Topology Visualizer" className="panel" style={{ padding: 0, overflow: 'hidden', marginBottom: 16 }}>
          <div
            style={{
              padding: '12px 20px',
              borderBottom: '1px solid #1e2c40',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexWrap: 'wrap',
              gap: 8,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ fontWeight: 800, color: '#f8fafc', fontSize: '0.92rem' }}>
                🌐 Live Network Topology Map
              </span>
              <span style={{ fontSize: '0.72rem', color: '#64748b' }}>
                (Hover over any router to inspect connected links)
              </span>
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8', display: 'flex', gap: 12 }}>
              <span>Routers: <strong style={{ color: '#10b981' }}>{activeNodes.length}</strong> / 8</span>
              <span>Links: <strong style={{ color: '#38bdf8' }}>{activeLinks.length}</strong> / 13</span>
              {topo.current_route && (
                <span>Route Hops: <strong style={{ color: '#00e5ff' }}>{topo.current_route.length - 1}</strong></span>
              )}
            </div>
          </div>

          <div style={{ width: '100%', height: 440, background: '#0b0f19' }}>
            <NetworkGraph
              nodes={topo.nodes}
              links={topo.links}
              currentRoute={topo.current_route}
              width={1350}
              height={440}
            />
          </div>
        </section>

        {/* Accessible Graph Legend */}
        <AccessibleLegend />

        {/* Active Route Step-by-Step Pills */}
        {topo.current_route && (
          <RoutePills route={topo.current_route} cost={topo.current_cost} />
        )}

        {/* ── Workspaces Tab Navigation ── */}
        <div style={{ marginTop: 24 }}>
          <div
            style={{
              display: 'flex',
              gap: 8,
              borderBottom: '1px solid #1e2c40',
              paddingBottom: 12,
              marginBottom: 18,
            }}
          >
            {[
              { id: 'failure', label: '⚡ Network Failure Testing (Self-Healing)' },
              { id: 'security', label: '🛡️ Security Testing (Route Request Gate)' },
              { id: 'logs', label: '📋 Network Event & Audit Logs' },
            ].map((t) => (
              <button
                key={t.id}
                className={`tab-btn ${activeTab === t.id ? 'active' : ''}`}
                onClick={() => setActiveTab(t.id as typeof activeTab)}
              >
                {t.label}
              </button>
            ))}
          </div>

          {/* TAB 1: NETWORK FAILURE TESTING */}
          {activeTab === 'failure' && (
            <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1.1fr', gap: 18 }}>
              {/* Left Column: Command & Control Studio */}
              <div className="panel">
                <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                  {[
                    { id: 'routing', label: 'Routing & Flow' },
                    { id: 'inject', label: 'Failure Injection' },
                    { id: 'recover', label: 'Recovery & Reset' },
                  ].map((sub) => (
                    <button
                      key={sub.id}
                      className={`tab-btn ${failSubTab === sub.id ? 'active' : ''}`}
                      style={{ fontSize: '0.75rem', padding: '6px 14px' }}
                      onClick={() => setFailSubTab(sub.id as typeof failSubTab)}
                    >
                      {sub.label}
                    </button>
                  ))}
                </div>

                {/* Subtab 1: Routing & Flow */}
                {failSubTab === 'routing' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                      Calculate the lowest-cost path between any two routers using Dijkstra&apos;s algorithm
                      and simulate virtual packet forwarding.
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <label htmlFor="select-src-router">Source Router</label>
                        <select
                          id="select-src-router"
                          value={sourceRouter}
                          onChange={(e) => setSourceRouter(e.target.value)}
                        >
                          {allNodeIds.map((id) => (
                            <option key={id} value={id}>
                              Router {id} {!activeNodes.some((n) => n.id === id) ? '(OFFLINE)' : ''}
                            </option>
                          ))}
                        </select>
                        {isSourceDown && (
                          <div style={{ fontSize: '0.7rem', color: '#f43f5e', marginTop: 4 }}>
                            ⚠️ Source Router {sourceRouter} is currently down
                          </div>
                        )}
                      </div>

                      <div>
                        <label htmlFor="select-dest-router">Destination Router</label>
                        <select
                          id="select-dest-router"
                          value={destRouter}
                          onChange={(e) => setDestRouter(e.target.value)}
                        >
                          {allNodeIds.map((id) => (
                            <option key={id} value={id}>
                              {id === 'H' ? 'Database (Router H)' : `Router ${id}`}{' '}
                              {!activeNodes.some((n) => n.id === id) ? '(OFFLINE)' : ''}
                            </option>
                          ))}
                        </select>
                        {isDestDown && (
                          <div style={{ fontSize: '0.7rem', color: '#f43f5e', marginTop: 4 }}>
                            ⚠️ Destination Router {destRouter} is currently down
                          </div>
                        )}
                      </div>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10, marginTop: 4 }}>
                      <button
                        className="btn-primary"
                        disabled={isActionLoading || sourceRouter === destRouter}
                        onClick={() =>
                          executeAction(
                            () => findRoute(sourceRouter, destRouter),
                            (res) => {
                              updateTopologyState(res.topology ?? res);
                              showToast(
                                `Route computed: ${(res.path as string[]).join(' → ')} | Cost: ${res.cost}`,
                                true
                              );
                            }
                          )
                        }
                      >
                        {isActionLoading ? 'Calculating...' : '🔍 Find Best Route (Dijkstra)'}
                      </button>

                      <button
                        className="btn-primary"
                        disabled={isActionLoading || !topo.current_route}
                        onClick={() =>
                          executeAction(
                            () => transmitPacket(),
                            (res) => {
                              updateTopologyState(res.topology ?? res);
                              showToast(
                                res.success
                                  ? '✅ Packet delivered successfully!'
                                  : '❌ Packet dropped in transit!',
                                res.success
                              );
                            }
                          )
                        }
                      >
                        {isActionLoading ? 'Transmitting...' : '🚀 Transmit Virtual Packet'}
                      </button>
                    </div>

                    {sourceRouter === destRouter && (
                      <div style={{ fontSize: '0.75rem', color: '#f59e0b' }}>
                        Source and Destination cannot be the same router.
                      </div>
                    )}
                  </div>
                )}

                {/* Subtab 2: Failure Injection */}
                {failSubTab === 'inject' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                      Inject physical network failures to test MeshGuard&apos;s autonomous self-healing and rerouting.
                    </div>

                    <div style={{ display: 'flex', gap: 8 }}>
                      <button
                        className={`tab-btn ${failType === 'link' ? 'active' : ''}`}
                        style={{ flex: 1 }}
                        onClick={() => setFailType('link')}
                      >
                        Sever Network Link
                      </button>
                      <button
                        className={`tab-btn ${failType === 'node' ? 'active' : ''}`}
                        style={{ flex: 1 }}
                        onClick={() => setFailType('node')}
                      >
                        Crash Router Node
                      </button>
                    </div>

                    {failType === 'link' ? (
                      <>
                        <div>
                          <label htmlFor="select-sever-link">Select Active Link to Sever</label>
                          {activeLinks.length === 0 ? (
                            <div style={{ color: '#64748b', fontSize: '0.8rem' }}>
                              All network links are currently severed.
                            </div>
                          ) : (
                            <select
                              id="select-sever-link"
                              value={selLink}
                              onChange={(e) => setSelLink(e.target.value)}
                            >
                              {activeLinks.map((l) => (
                                <option key={`${l.source}-${l.target}`} value={`${l.source}-${l.target}`}>
                                  Link {l.source} ↔ {l.target} (cost: {l.weight})
                                </option>
                              ))}
                            </select>
                          )}
                        </div>

                        <button
                          className="btn-danger"
                          disabled={isActionLoading || !selLink}
                          onClick={() => {
                            const [u, v] = selLink.split('-');
                            executeAction(
                              () => failLink(u, v),
                              (res) => {
                                updateTopologyState(res);
                                showToast(`Link ${u}-${v} severed! Self-healing triggered.`, false);
                              }
                            );
                          }}
                        >
                          💥 Sever Selected Link
                        </button>
                      </>
                    ) : (
                      <>
                        <div>
                          <label htmlFor="select-crash-router">Select Router to Crash</label>
                          {activeNodes.length === 0 ? (
                            <div style={{ color: '#64748b', fontSize: '0.8rem' }}>
                              All routers are currently down.
                            </div>
                          ) : (
                            <select
                              id="select-crash-router"
                              value={selNode}
                              onChange={(e) => setSelNode(e.target.value)}
                            >
                              {activeNodes.map((n) => (
                                <option key={n.id} value={n.id}>
                                  Router {n.id} {n.id === 'H' ? '(Database Destination)' : ''}
                                </option>
                              ))}
                            </select>
                          )}
                        </div>

                        <button
                          className="btn-danger"
                          disabled={isActionLoading || !selNode}
                          onClick={() => {
                            executeAction(
                              () => failNode(selNode),
                              (res) => {
                                updateTopologyState(res);
                                showToast(
                                  `Router ${selNode} crashed! Connected links disabled.`,
                                  false
                                );
                              }
                            );
                          }}
                        >
                          🛑 Crash Selected Router
                        </button>
                      </>
                    )}
                  </div>
                )}

                {/* Subtab 3: Recovery & Reset */}
                {failSubTab === 'recover' && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                    <div style={{ fontSize: '0.82rem', color: '#94a3b8' }}>
                      Restore severed links, power up crashed routers, or perform a complete network topology reset.
                    </div>

                    <div>
                      <label htmlFor="select-restore-link">Restore Severed Link</label>
                      {failedLinks.length === 0 ? (
                        <div style={{ color: '#10b981', fontSize: '0.78rem' }}>
                          ✔ All network links are currently operational.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: 8 }}>
                          <select
                            id="select-restore-link"
                            value={selRestLink}
                            onChange={(e) => setSelRestLink(e.target.value)}
                            style={{ flex: 1 }}
                          >
                            {failedLinks.map((l) => (
                              <option key={`${l.source}-${l.target}`} value={`${l.source}-${l.target}`}>
                                Severed Link {l.source} ↔ {l.target} (cost: {l.weight})
                              </option>
                            ))}
                          </select>
                          <button
                            className="btn-primary"
                            style={{ width: 'auto', padding: '0 16px' }}
                            disabled={isActionLoading || !selRestLink}
                            onClick={() => {
                              const [u, v] = selRestLink.split('-');
                              executeAction(
                                () => restoreLink(u, v),
                                (res) => {
                                  updateTopologyState(res);
                                  showToast(`Link ${u}-${v} restored to service`, true);
                                }
                              );
                            }}
                          >
                            🔄 Restore Link
                          </button>
                        </div>
                      )}
                    </div>

                    <hr style={{ border: 'none', borderTop: '1px solid #1e2c40', margin: '4px 0' }} />

                    <div>
                      <label htmlFor="select-restore-router">Power Up Crashed Router</label>
                      {failedNodes.length === 0 ? (
                        <div style={{ color: '#10b981', fontSize: '0.78rem' }}>
                          ✔ All routers are currently online.
                        </div>
                      ) : (
                        <div style={{ display: 'flex', gap: 8 }}>
                          <select
                            id="select-restore-router"
                            value={selRestNode}
                            onChange={(e) => setSelRestNode(e.target.value)}
                            style={{ flex: 1 }}
                          >
                            {failedNodes.map((n) => (
                              <option key={n.id} value={n.id}>
                                Crashed Router {n.id}
                              </option>
                            ))}
                          </select>
                          <button
                            className="btn-primary"
                            style={{ width: 'auto', padding: '0 16px' }}
                            disabled={isActionLoading || !selRestNode}
                            onClick={() => {
                              executeAction(
                                () => restoreNode(selRestNode),
                                (res) => {
                                  updateTopologyState(res);
                                  showToast(`Router ${selRestNode} powered up and online`, true);
                                }
                              );
                            }}
                          >
                            🔄 Power Up
                          </button>
                        </div>
                      )}
                    </div>

                    <hr style={{ border: 'none', borderTop: '1px solid #1e2c40', margin: '4px 0' }} />

                    <button
                      className="btn-ghost"
                      disabled={isActionLoading}
                      onClick={() => {
                        executeAction(
                          resetNetwork,
                          (res) => {
                            updateTopologyState(res);
                            showToast('Full network topology reset to pristine baseline', true);
                          }
                        );
                      }}
                    >
                      ♻ Reset Entire Network (All Routers & Links)
                    </button>
                  </div>
                )}
              </div>

              {/* Right Column: Route Breakdown & Hop Telemetry */}
              <div className="panel">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                  <div style={{ fontWeight: 800, color: '#f8fafc', fontSize: '0.92rem' }}>
                    📌 Route Breakdown & Hop Telemetry
                  </div>
                  {topo.current_cost !== null && (
                    <span className="badge badge-cyan">
                      Cost: {topo.current_cost}
                    </span>
                  )}
                </div>

                {topo.route_hops.length > 0 ? (
                  <div style={{ overflowX: 'auto', marginBottom: 16 }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
                      <thead>
                        <tr style={{ color: '#64748b', textAlign: 'left', borderBottom: '1px solid #1e2c40' }}>
                          <th style={{ padding: '6px 8px' }}>Hop</th>
                          <th style={{ padding: '6px 8px' }}>From</th>
                          <th style={{ padding: '6px 8px' }}>To</th>
                          <th style={{ padding: '6px 8px' }}>Link Weight</th>
                          <th style={{ padding: '6px 8px' }}>Cumulative</th>
                        </tr>
                      </thead>
                      <tbody>
                        {topo.route_hops.map((h) => (
                          <tr key={h.hop} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                            <td style={{ padding: '6px 8px', color: '#94a3b8' }}>#{h.hop}</td>
                            <td style={{ padding: '6px 8px', color: '#00e5ff', fontFamily: 'monospace' }}>
                              Router {h.from}
                            </td>
                            <td style={{ padding: '6px 8px', color: '#00e5ff', fontFamily: 'monospace' }}>
                              Router {h.to}
                            </td>
                            <td style={{ padding: '6px 8px', color: '#f8fafc' }}>{h.cost}</td>
                            <td style={{ padding: '6px 8px', color: '#10b981', fontWeight: 700 }}>
                              {h.cumulative_cost}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div
                    style={{
                      background: '#080c14',
                      border: '1px solid #1e2c40',
                      borderRadius: 8,
                      padding: '16px',
                      color: '#64748b',
                      fontSize: '0.78rem',
                      textAlign: 'center',
                      marginBottom: 16,
                    }}
                  >
                    No active route computed. Click <strong>&quot;Find Best Route&quot;</strong> to view hop telemetry.
                  </div>
                )}

                {/* Hop Telemetry Stream */}
                {topo.packet_logs.length > 0 && (
                  <div>
                    <div style={{ fontWeight: 700, color: '#f8fafc', marginBottom: 6, fontSize: '0.82rem' }}>
                      📦 Virtual Packet Forwarding Telemetry Stream
                    </div>
                    <div
                      style={{
                        background: '#080c14',
                        border: '1px solid #1e2c40',
                        borderRadius: 8,
                        padding: '10px 14px',
                        fontFamily: 'monospace',
                        fontSize: '0.76rem',
                        lineHeight: 1.6,
                        maxHeight: 160,
                        overflowY: 'auto',
                      }}
                    >
                      {topo.packet_logs.map((log, i) => (
                        <div
                          key={i}
                          style={{
                            color: log.includes('[OK]')
                              ? '#10b981'
                              : log.includes('[FAIL]') || log.includes('dropped')
                              ? '#f43f5e'
                              : '#38bdf8',
                            fontWeight: log.includes('[OK]') || log.includes('[FAIL]') ? 700 : 400,
                          }}
                        >
                          {log}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* TAB 2: SECURITY TESTING (ROUTE REQUEST GATE) */}
          {activeTab === 'security' && (
            <SecurityPanel topo={topo} onUpdate={updateTopologyState} />
          )}

          {/* TAB 3: NETWORK EVENT & AUDIT LOGS */}
          {activeTab === 'logs' && <LogsPanel logs={topo.event_logs} />}
        </div>
      </main>

      {/* ── Footer ── */}
      <footer
        style={{
          textAlign: 'center',
          padding: '24px 0 36px',
          borderTop: '1px solid #1e2c40',
          color: '#64748b',
          fontSize: '0.74rem',
        }}
      >
        <div style={{ fontWeight: 600, color: '#94a3b8', marginBottom: 4 }}>
          MESHGUARD · SECURE SELF-HEALING COMPUTER NETWORK SIMULATOR
        </div>
        <div>
          Autonomous Dijkstra Dynamic Routing & Route Policy Gate · College Computer Networks Mini-Project
        </div>
      </footer>
    </div>
  );
}
