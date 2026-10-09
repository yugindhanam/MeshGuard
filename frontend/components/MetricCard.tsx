import React from 'react';

interface Props {
  title: string;
  value: string;
  sub?: string;
  tone?: 'cyan' | 'green' | 'red' | 'amber';
  icon?: string;
}

export default function MetricCard({ title, value, sub, tone = 'cyan', icon }: Props) {
  const colors: Record<string, string> = {
    cyan: '#00e5ff', green: '#10b981', red: '#f43f5e', amber: '#f59e0b',
  };
  const color = colors[tone];
  return (
    <div className={`metric-card ${tone}`}>
      <div style={{ fontSize: '0.72rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>
        {icon && <span style={{ marginRight: 6 }}>{icon}</span>}{title}
      </div>
      <div style={{ fontSize: '1.45rem', fontWeight: 800, color, fontFamily: 'monospace', lineHeight: 1.2 }}>
        {value}
      </div>
      {sub && <div style={{ fontSize: '0.72rem', color: '#64748b', marginTop: 4 }}>{sub}</div>}
    </div>
  );
}
