'use client';
import React, { useState, useMemo } from 'react';
import type { LogEntry } from '@/lib/types';

interface ParsedLog {
  timestamp: string;
  severity: 'SECURITY ALERT' | 'ERROR' | 'WARNING' | 'INFO';
  badgeColor: string;
  badgeBg: string;
  badgeBorder: string;
  category: string;
  cleanMessage: string;
  raw: string;
}

function parseLog(entry: LogEntry): ParsedLog {
  const msg = entry.message;
  let severity: ParsedLog['severity'] = 'INFO';
  let category = 'SYSTEM';

  if (msg.includes('[SECURITY]') && (msg.includes('MALICIOUS') || msg.includes('SUSPICIOUS') || msg.includes('blocked') || msg.includes('penalty'))) {
    severity = 'SECURITY ALERT';
    category = 'SECURITY';
  } else if (msg.includes('[FAIL]') || msg.includes('dropped') || msg.includes('Partitioned') || msg.includes('down') || msg.includes('offline')) {
    severity = 'ERROR';
    category = 'FAILURE';
  } else if (msg.includes('[MONITOR]') || msg.includes('degraded') || msg.includes('compromised')) {
    severity = 'WARNING';
    category = 'MONITOR';
  } else if (msg.includes('[HEAL]')) {
    severity = 'INFO';
    category = 'SELF-HEALING';
  } else if (msg.includes('[ROUTE]')) {
    severity = 'INFO';
    category = 'ROUTING';
  } else if (msg.includes('[PACKET]')) {
    severity = 'INFO';
    category = 'PACKET';
  } else if (msg.includes('[RESTORE]')) {
    severity = 'INFO';
    category = 'RESTORE';
  }

  const styles: Record<ParsedLog['severity'], { color: string; bg: string; border: string }> = {
    'SECURITY ALERT': { color: '#fb7185', bg: 'rgba(251, 113, 133, 0.15)', border: 'rgba(251, 113, 133, 0.4)' },
    'ERROR': { color: '#f43f5e', bg: 'rgba(244, 63, 94, 0.15)', border: 'rgba(244, 63, 94, 0.4)' },
    'WARNING': { color: '#f59e0b', bg: 'rgba(245, 158, 11, 0.15)', border: 'rgba(245, 158, 11, 0.4)' },
    'INFO': { color: '#38bdf8', bg: 'rgba(56, 189, 248, 0.12)', border: 'rgba(56, 189, 248, 0.3)' },
  };

  const cleanMessage = msg.replace(/\[(SYS|ROUTE|PACKET|FAIL|HEAL|MONITOR|SECURITY|RESTORE|RESET)\]\s*/g, '').trim();

  return {
    timestamp: entry.timestamp,
    severity,
    badgeColor: styles[severity].color,
    badgeBg: styles[severity].bg,
    badgeBorder: styles[severity].border,
    category,
    cleanMessage,
    raw: msg,
  };
}

export default function LogsPanel({ logs }: { logs: LogEntry[] }) {
  const [filterSeverity, setFilterSeverity] = useState<string>('All Severities');
  const [searchTerm, setSearchTerm] = useState<string>('');

  const parsedLogs = useMemo(() => {
    return [...logs].reverse().map(parseLog);
  }, [logs]);

  const filtered = useMemo(() => {
    return parsedLogs.filter((l) => {
      if (filterSeverity !== 'All Severities' && l.severity !== filterSeverity) {
        return false;
      }
      if (searchTerm.trim() && !l.raw.toLowerCase().includes(searchTerm.toLowerCase())) {
        return false;
      }
      return true;
    });
  }, [parsedLogs, filterSeverity, searchTerm]);

  return (
    <div className="panel" style={{ marginTop: 8 }}>
      {/* Panel Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div style={{ fontSize: '0.72rem', color: '#00e5ff', fontWeight: 700, letterSpacing: '0.08em' }}>
            TELEMETRY AUDIT TRAIL
          </div>
          <h4 style={{ fontSize: '1.1rem', fontWeight: 800, color: '#f8fafc', margin: '2px 0 0 0' }}>
            Network Event & Security Audit Logs
          </h4>
        </div>
        <div style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
          Showing <strong>{filtered.length}</strong> of {parsedLogs.length} events
        </div>
      </div>

      {/* Filter Toolbar */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
        <div style={{ minWidth: 180 }}>
          <select
            value={filterSeverity}
            onChange={(e) => setFilterSeverity(e.target.value)}
            aria-label="Filter logs by severity"
          >
            <option>All Severities</option>
            <option>SECURITY ALERT</option>
            <option>ERROR</option>
            <option>WARNING</option>
            <option>INFO</option>
          </select>
        </div>

        <div style={{ flex: 1, minWidth: 220 }}>
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search audit trail (e.g. Router D, Client 2, Link, Dijkstra)..."
            aria-label="Search logs"
          />
        </div>

        {searchTerm && (
          <button
            className="tab-btn"
            style={{ fontSize: '0.75rem', padding: '6px 12px' }}
            onClick={() => setSearchTerm('')}
          >
            Clear Search
          </button>
        )}
      </div>

      {/* Table / List View */}
      <div
        style={{
          background: '#080c14',
          border: '1px solid #1e2c40',
          borderRadius: 8,
          overflow: 'hidden',
        }}
      >
        <div
          style={{
            maxHeight: 380,
            overflowY: 'auto',
          }}
        >
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.78rem' }}>
            <thead>
              <tr style={{ background: '#0e1726', color: '#64748b', textAlign: 'left', borderBottom: '1px solid #1e2c40' }}>
                <th style={{ padding: '8px 12px', width: 90 }}>Time</th>
                <th style={{ padding: '8px 12px', width: 140 }}>Severity</th>
                <th style={{ padding: '8px 12px', width: 110 }}>Category</th>
                <th style={{ padding: '8px 12px' }}>Event Description</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((log, idx) => (
                <tr
                  key={idx}
                  style={{
                    borderBottom: '1px solid rgba(255,255,255,0.03)',
                    background: idx % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.01)',
                  }}
                >
                  <td style={{ padding: '8px 12px', color: '#64748b', fontFamily: 'monospace' }}>
                    {log.timestamp}
                  </td>
                  <td style={{ padding: '8px 12px' }}>
                    <span
                      style={{
                        display: 'inline-block',
                        fontSize: '0.68rem',
                        fontWeight: 700,
                        padding: '2px 8px',
                        borderRadius: 4,
                        color: log.badgeColor,
                        background: log.badgeBg,
                        border: `1px solid ${log.badgeBorder}`,
                      }}
                    >
                      {log.severity}
                    </span>
                  </td>
                  <td style={{ padding: '8px 12px', color: '#94a3b8', fontSize: '0.72rem', fontFamily: 'monospace' }}>
                    [{log.category}]
                  </td>
                  <td style={{ padding: '8px 12px', color: '#f8fafc', lineHeight: 1.45 }}>
                    {log.cleanMessage}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ padding: 24, textAlign: 'center', color: '#64748b' }}>
                    No audit log records match the current filter criteria.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
