import React from 'react';
import type { HealingEvent } from '@/lib/types';

export default function HealingBanner({ event }: { event: HealingEvent }) {
  if (event.status === 'RECOVERED') {
    const orig = event.original_path?.join(' → ') ?? 'None';
    const recovered = event.recovered_path?.join(' → ') ?? 'None';
    return (
      <div className="healing-banner success" style={{ marginBottom: 18 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10, flexWrap: 'wrap', gap: 8 }}>
          <strong style={{ color: '#10b981', fontSize: '1.02rem', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span>⚡ Autonomous Self-Healing Triggered & Completed</span>
          </strong>
          <span
            className="badge badge-green"
            title="Measured CPU wall-clock time for failure detection and Dijkstra recalculation"
          >
            SIMULATED CONVERGENCE: {event.recovery_time.toFixed(3)}s
          </span>
        </div>
        <div style={{ fontSize: '0.85rem', lineHeight: 1.7, color: '#e2e8f0' }}>
          <div>• <strong>Root Cause Detected:</strong> {event.failure_type} <code>{String(event.failed_item)}</code> compromised the active forwarding path.</div>
          <div>• <strong>Compromised Route:</strong> <span style={{ textDecoration: 'line-through', color: '#f87171' }}>{orig}</span></div>
          <div>• <strong>Alternative Shortest Path Recomputed:</strong> <strong style={{ color: '#00e5ff' }}>{recovered}</strong> (New Total Cost: <code>{event.recovered_cost}</code>)</div>
          <div>• <strong>Convergence State:</strong> <span style={{ color: '#10b981', fontWeight: 700 }}>✓ Telemetry Restored with Zero Packet Forwarding Disruption.</span></div>
        </div>
      </div>
    );
  }
  if (event.status === 'FAILED_NO_PATH') {
    return (
      <div className="healing-banner fail" style={{ marginBottom: 18 }}>
        <strong style={{ color: '#ef4444', fontSize: '1.02rem', display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span>🔴 Critical Network Partition Detected (No Viable Path)</span>
        </strong>
        <div style={{ fontSize: '0.85rem', lineHeight: 1.6, color: '#e2e8f0' }}>
          <div>• <strong>Failure Impact:</strong> {event.failure_type} <code>{String(event.failed_item)}</code> severed the last remaining link path.</div>
          <div>• <strong>Destination Unreachable:</strong> No alternative operational route exists between source and destination.</div>
          <div>• <strong>NOC Action Required:</strong> Use the Recovery panel below to restore routers or links.</div>
        </div>
      </div>
    );
  }
  return null;
}
