'use client';
import React from 'react';

interface Props {
  route: string[];
  cost: number | null;
}

export default function RoutePills({ route, cost }: Props) {
  if (!route || route.length === 0) return null;

  const hopsCount = route.length - 1;
  const sourceNode = route[0];
  const destNode = route[route.length - 1];

  return (
    <div
      style={{
        background: '#080c14',
        border: '1px solid #1e3a5f',
        borderRadius: 12,
        padding: '16px 20px',
        marginTop: 14,
        marginBottom: 10,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          flexWrap: 'wrap',
          gap: 10,
          marginBottom: 12,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span style={{ fontSize: '1rem' }}>📍</span>
          <span
            style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              color: '#94a3b8',
              textTransform: 'uppercase',
              letterSpacing: '0.06em',
            }}
          >
            Active Dijkstra Shortest Route (Verified Loop-Free)
          </span>
        </div>

        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <span
            style={{
              fontFamily: 'monospace',
              fontWeight: 700,
              fontSize: '0.75rem',
              color: '#38bdf8',
              background: 'rgba(56, 189, 248, 0.12)',
              border: '1px solid rgba(56, 189, 248, 0.3)',
              padding: '3px 10px',
              borderRadius: 6,
            }}
          >
            Total Metric Cost: {cost !== null ? cost : 'N/A'}
          </span>
          <span
            style={{
              fontFamily: 'monospace',
              fontWeight: 700,
              fontSize: '0.75rem',
              color: '#10b981',
              background: 'rgba(16, 185, 129, 0.12)',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              padding: '3px 10px',
              borderRadius: 6,
            }}
          >
            Hop Count: {hopsCount}
          </span>
          <span
            style={{
              fontSize: '0.7rem',
              color: '#64748b',
            }}
          >
            ({sourceNode} ➔ {destNode})
          </span>
        </div>
      </div>

      {/* Step by step pills */}
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6 }}>
        {route.map((node, i) => {
          const isSource = i === 0;
          const isDest = i === route.length - 1;
          const isDb = node === 'H';

          return (
            <React.Fragment key={`${node}-${i}`}>
              <span
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                  padding: '5px 12px',
                  borderRadius: 20,
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  fontFamily: 'monospace',
                  background: isDest
                    ? 'rgba(168, 85, 247, 0.18)'
                    : isSource
                    ? 'rgba(16, 185, 129, 0.18)'
                    : 'rgba(0, 229, 255, 0.12)',
                  border: `1px solid ${
                    isDest ? '#a855f7' : isSource ? '#10b981' : '#00e5ff'
                  }`,
                  color: isDest ? '#c084fc' : isSource ? '#34d399' : '#00e5ff',
                }}
              >
                <span>{isSource ? '🟢' : isDest ? '🗄️' : '●'}</span>
                <span>{isDb ? `Database (${node})` : `Router ${node}`}</span>
                {isSource && (
                  <span style={{ fontSize: '0.65rem', opacity: 0.8, textTransform: 'uppercase' }}>[SRC]</span>
                )}
                {isDest && (
                  <span style={{ fontSize: '0.65rem', opacity: 0.8, textTransform: 'uppercase' }}>[DEST]</span>
                )}
              </span>

              {i < route.length - 1 && (
                <span
                  style={{
                    color: '#00e5ff',
                    fontWeight: 700,
                    fontSize: '0.9rem',
                    margin: '0 2px',
                  }}
                  aria-hidden="true"
                >
                  ──►
                </span>
              )}
            </React.Fragment>
          );
        })}
      </div>
    </div>
  );
}
