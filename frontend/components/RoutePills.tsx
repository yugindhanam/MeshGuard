import React from 'react';

export default function RoutePills({ route, cost }: { route: string[]; cost: number | null }) {
  if (!route.length) return null;
  return (
    <div style={{
      background: '#080c14', border: '1px solid #1e2c40', borderRadius: 10,
      padding: '14px 18px', marginTop: 12,
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
        <span style={{ fontSize: '0.72rem', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase' }}>Active Verified Route</span>
        {cost !== null && (
          <span className="badge badge-cyan">
            Cost: {cost} | Hops: {route.length - 1}
          </span>
        )}
      </div>
      <div style={{ display: 'flex', flexWrap: 'wrap', alignItems: 'center', gap: 6 }}>
        {route.map((node, i) => (
          <React.Fragment key={node}>
            <span className="route-pill">{node === 'H' ? `DB (${node})` : `Router ${node}`}</span>
            {i < route.length - 1 && <span style={{ color: '#334155', fontSize: '1rem' }}>──►</span>}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
}
