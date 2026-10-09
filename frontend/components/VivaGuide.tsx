'use client';
import React, { useState } from 'react';

export default function VivaGuide() {
  const [isExpanded, setIsExpanded] = useState(false);

  const steps = [
    {
      num: '01',
      title: 'Start with Healthy Mesh',
      desc: 'Show the initial 8-router topology: all 8 routers and 13 links online. Three clients are initialized with normal reputation.',
    },
    {
      num: '02',
      title: 'Compute Baseline Shortest Path',
      desc: 'Select Source A and Destination H. Click "Find Best Route" to calculate the optimal path A → B → D → F → H (Cost: 10, 4 hops).',
    },
    {
      num: '03',
      title: 'Simulate Virtual Packet Flow',
      desc: 'Click "Transmit Packet" to observe hop-by-hop packet forwarding along the active path with 100% delivery rate.',
    },
    {
      num: '04',
      title: 'Inject Network Failure',
      desc: 'Switch to "Failure Injection", select active Link D-F (or crash Router D), and click "Sever Link".',
    },
    {
      num: '05',
      title: 'Observe Autonomous Self-Healing',
      desc: 'Watch the self-healing banner appear: MeshGuard detects the severed link in milliseconds and recomputes the alternative path A → B → D → H.',
    },
    {
      num: '06',
      title: 'Test Restoration & Reset',
      desc: 'Use "Restore Selected Link" to bring link D-F back online, updating the routing table to the lowest-cost baseline.',
    },
    {
      num: '07',
      title: 'Simulate Malicious Route Attack',
      desc: 'Switch to "Security Testing", select Client 2, and click "Simulate Attack" (proposing a rogue path via "Unauthorized X").',
    },
    {
      num: '08',
      title: 'Show Threat Gate Rejection',
      desc: 'Highlight the incident lifecycle: the rogue proposal is blocked before packet forwarding. Client 2 trust score is penalized.',
    },
    {
      num: '09',
      title: 'Verify Unaffected Normal Clients',
      desc: 'Show that Client 1 and Client 3 remain at 100 Trust Score with normal operational status throughout the incident.',
    },
  ];

  return (
    <div
      style={{
        background: '#0c1424',
        border: '1px solid #1e3a5f',
        borderRadius: 12,
        padding: '16px 20px',
        marginBottom: 20,
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          cursor: 'pointer',
        }}
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <span style={{ fontSize: '1.2rem' }}>🎓</span>
          <div>
            <div style={{ fontSize: '0.92rem', fontWeight: 800, color: '#f8fafc' }}>
              9-Step Viva & Lab Demonstration Guide
            </div>
            <div style={{ fontSize: '0.74rem', color: '#94a3b8' }}>
              Structured presentation sequence for explaining dynamic routing, self-healing, and route security
            </div>
          </div>
        </div>
        <button
          className="tab-btn"
          style={{
            fontSize: '0.75rem',
            padding: '4px 12px',
            color: '#38bdf8',
            borderColor: 'rgba(56, 189, 248, 0.4)',
          }}
          onClick={(e) => {
            e.stopPropagation();
            setIsExpanded(!isExpanded);
          }}
        >
          {isExpanded ? 'Hide Steps ▲' : 'Show Viva Steps ▼'}
        </button>
      </div>

      {isExpanded && (
        <div style={{ marginTop: 18, borderTop: '1px solid #1e2c40', paddingTop: 16 }}>
          <div
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))',
              gap: 12,
            }}
          >
            {steps.map((s) => (
              <div
                key={s.num}
                style={{
                  background: '#080c14',
                  border: '1px solid #1e2c40',
                  borderRadius: 8,
                  padding: '12px 14px',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                  <span
                    style={{
                      background: 'rgba(0, 229, 255, 0.15)',
                      color: '#00e5ff',
                      fontSize: '0.7rem',
                      fontWeight: 800,
                      padding: '2px 6px',
                      borderRadius: 4,
                      fontFamily: 'monospace',
                    }}
                  >
                    STEP {s.num}
                  </span>
                  <strong style={{ fontSize: '0.82rem', color: '#f8fafc' }}>{s.title}</strong>
                </div>
                <p style={{ fontSize: '0.75rem', color: '#94a3b8', margin: 0, lineHeight: 1.45 }}>
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
