import React from 'react';
import type { HealingEvent } from '@/lib/types';

export default function HealingBanner({ event }: { event: HealingEvent }) {
  if (event.status === 'RECOVERED') {
    const orig = event.original_path?.join(' → ') ?? 'None';
    const recovered = event.recovered_path?.join(' → ') ?? 'None';
    return (
      <div className="healing-banner success">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <strong style={{ color: '#10b981', fontSize: '1rem' }}>⚡ Autonomous Self-Healing Completed</strong>
          <span className="badge badge-green">RECOVERY: {event.recovery_time.toFixed(3)}s</span>
        </div>
        <div style={{ fontSize: '0.85rem', lineHeight: 1.7, color: '#e2e8f0' }}>
          <div>• <strong>Root Cause:</strong> {event.failure_type} <code>{String(event.failed_item)}</code> compromised active path.</div>
          <div>• <strong>Compromised Route:</strong> <span style={{ textDecoration: 'line-through', color: '#f87171' }}>{orig}</span></div>
          <div>• <strong>Alternative Path:</strong> <span style={{ color: '#00e5ff', fontWeight: 700 }}>{recovered}</span> (Cost: {event.recovered_cost})</div>
          <div>• <strong>Status:</strong> <span style={{ color: '#10b981', fontWeight: 700 }}>✓ Network Restored with Zero Downtime</span></div>
        </div>
      </div>
    );
  }
  if (event.status === 'FAILED_NO_PATH') {
    return (
      <div className="healing-banner fail">
        <strong style={{ color: '#ef4444', fontSize: '1rem', display: 'block', marginBottom: 8 }}>🔴 Critical Network Partition Detected</strong>
        <div style={{ fontSize: '0.85rem', lineHeight: 1.6, color: '#e2e8f0' }}>
          <div>• <strong>Impact:</strong> {event.failure_type} <code>{String(event.failed_item)}</code> severed all remaining paths.</div>
          <div>• <strong>Destination Unreachable:</strong> No alternative operational route exists.</div>
          <div>• <strong>Action Required:</strong> Restore routers or links in the Recovery panel.</div>
        </div>
      </div>
    );
  }
  return null;
}
