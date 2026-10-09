import React from 'react';

interface Props {
  title: string;
  value: string;
  sub?: string;
  tone?: 'cyan' | 'green' | 'red' | 'amber';
  icon?: string;
  badge?: string;
  tooltip?: string;
}

export default function MetricCard({
  title,
  value,
  sub,
  tone = 'cyan',
  icon,
  badge,
  tooltip,
}: Props) {
  const colors: Record<string, { main: string; bg: string; border: string }> = {
    cyan: { main: '#00e5ff', bg: 'rgba(0, 229, 255, 0.08)', border: 'rgba(0, 229, 255, 0.25)' },
    green: { main: '#10b981', bg: 'rgba(16, 185, 129, 0.08)', border: 'rgba(16, 185, 129, 0.25)' },
    red: { main: '#f43f5e', bg: 'rgba(244, 63, 94, 0.08)', border: 'rgba(244, 63, 94, 0.25)' },
    amber: { main: '#f59e0b', bg: 'rgba(245, 158, 11, 0.08)', border: 'rgba(245, 158, 11, 0.25)' },
  };

  const scheme = colors[tone] || colors.cyan;

  return (
    <div
      className={`metric-card ${tone}`}
      title={tooltip}
      style={{
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        position: 'relative',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6 }}>
        <span
          style={{
            fontSize: '0.72rem',
            fontWeight: 700,
            color: '#94a3b8',
            textTransform: 'uppercase',
            letterSpacing: '0.06em',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
          }}
        >
          {icon && <span>{icon}</span>}
          {title}
        </span>
        {badge && (
          <span
            style={{
              fontSize: '0.65rem',
              fontWeight: 800,
              padding: '2px 6px',
              borderRadius: 4,
              backgroundColor: scheme.bg,
              border: `1px solid ${scheme.border}`,
              color: scheme.main,
              textTransform: 'uppercase',
            }}
          >
            {badge}
          </span>
        )}
      </div>

      <div
        style={{
          fontSize: '1.45rem',
          fontWeight: 800,
          color: scheme.main,
          fontFamily: 'monospace',
          lineHeight: 1.2,
          margin: '4px 0',
        }}
      >
        {value}
      </div>

      {sub && (
        <div style={{ fontSize: '0.73rem', color: '#64748b', display: 'flex', alignItems: 'center', gap: 4 }}>
          {sub}
        </div>
      )}
    </div>
  );
}
