'use client';
import React, { useState } from 'react';
import type { LogEntry } from '@/lib/types';

const SEVERITY_MAP: Record<string, string> = {
  '[FAIL]': 'red', '[HEAL]': 'green', '[SECURITY]': '#fb7185',
  '[ROUTE]': 'cyan', '[RESTORE]': '#a78bfa', '[PACKET]': '#fbbf24',
};

function getColor(msg: string) {
  for (const [key, color] of Object.entries(SEVERITY_MAP)) {
    if (msg.includes(key)) return color;
  }
  return '#94a3b8';
}

function getSeverity(msg: string) {
  if (msg.includes('[SECURITY]') && (msg.includes('MALICIOUS') || msg.includes('blocked'))) return 'SECURITY ALERT';
  if (msg.includes('[FAIL]') || msg.includes('dropped')) return 'ERROR';
  if (msg.includes('[MONITOR]') || msg.includes('degraded')) return 'WARNING';
  return 'INFO';
}

export default function LogsPanel({ logs }: { logs: LogEntry[] }) {
  const [filter, setFilter] = useState('All');
  const [search, setSearch] = useState('');
  const severities = ['All', 'SECURITY ALERT', 'ERROR', 'WARNING', 'INFO'];
  const reversed = [...logs].reverse();
  const filtered = reversed.filter((l) => {
    const sev = getSeverity(l.message);
    if (filter !== 'All' && sev !== filter) return false;
    if (search && !l.message.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div className="panel" style={{ marginTop: 24 }}>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16, flexWrap: 'wrap', alignItems: 'center' }}>
        <span style={{ fontSize: '1rem', fontWeight: 700, color: '#f8fafc' }}>📋 Network Audit & Event Logs</span>
        <select value={filter} onChange={(e) => setFilter(e.target.value)} style={{ width: 180, flex: 'none' }}>
          {severities.map((s) => <option key={s}>{s}</option>)}
        </select>
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search logs..."
          style={{ flex: 1, minWidth: 180 }}
        />
      </div>
      <div style={{
        background: '#080c14', borderRadius: 8, padding: '10px 14px',
        fontFamily: 'monospace', fontSize: '0.78rem', maxHeight: 280, overflowY: 'auto',
      }}>
        {filtered.slice(0, 80).map((l, i) => (
          <div key={i} className="log-row" style={{ color: getColor(l.message) }}>
            <span style={{ color: '#475569', marginRight: 8 }}>[{l.timestamp}]</span>
            {l.message}
          </div>
        ))}
        {filtered.length === 0 && <div style={{ color: '#475569' }}>No log entries match the filter.</div>}
      </div>
    </div>
  );
}
