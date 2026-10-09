'use client';
import React, { useState } from 'react';

export default function TerminologyModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="tab-btn"
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 6,
          background: 'rgba(56, 189, 248, 0.1)',
          borderColor: 'rgba(56, 189, 248, 0.3)',
          color: '#38bdf8',
          fontSize: '0.78rem',
          padding: '6px 14px',
        }}
        aria-label="Open Computer Networks Terminology Guide"
      >
        <span>📘</span>
        <span>Networking Terms Guide</span>
      </button>

      {isOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 9999,
            backgroundColor: 'rgba(5, 8, 15, 0.85)',
            backdropFilter: 'blur(8px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 20,
          }}
          onClick={() => setIsOpen(false)}
        >
          <div
            style={{
              backgroundColor: '#0f172a',
              border: '1px solid #1e2c40',
              borderRadius: 14,
              maxWidth: 780,
              width: '100%',
              maxHeight: '90vh',
              overflowY: 'auto',
              padding: 28,
              boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.7)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
              <div>
                <div style={{ fontSize: '0.72rem', color: '#00e5ff', fontWeight: 700, letterSpacing: '0.08em' }}>
                  COMPUTER NETWORKS VIVA REFERENCE
                </div>
                <h3 style={{ fontSize: '1.25rem', fontWeight: 800, color: '#f8fafc', margin: '4px 0 0 0' }}>
                  Technical Terminology & Metrics Guide
                </h3>
              </div>
              <button
                onClick={() => setIsOpen(false)}
                style={{
                  background: 'transparent',
                  border: 'none',
                  color: '#94a3b8',
                  fontSize: '1.5rem',
                  cursor: 'pointer',
                  padding: 4,
                  lineHeight: 1,
                }}
              >
                ✕
              </button>
            </div>

            <p style={{ color: '#94a3b8', fontSize: '0.84rem', lineHeight: 1.6, marginBottom: 22 }}>
              Use this glossary during viva presentations to clearly distinguish real simulation measurements
              from theoretical networking concepts.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
              <div style={{ background: '#080c14', padding: 16, borderRadius: 10, border: '1px solid #1e2c40' }}>
                <div style={{ fontWeight: 700, color: '#00e5ff', fontSize: '0.9rem', marginBottom: 6 }}>
                  ⚡ Dijkstra&apos;s Shortest Path
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                  A graph search algorithm that finds the path with the minimum total link weight between source and
                  destination routers. Implemented with a min-priority queue with time complexity $O((V + E) \log V)$.
                </p>
              </div>

              <div style={{ background: '#080c14', padding: 16, borderRadius: 10, border: '1px solid #1e2c40' }}>
                <div style={{ fontWeight: 700, color: '#10b981', fontSize: '0.9rem', marginBottom: 6 }}>
                  📊 Route Cost (Metric Weight)
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                  The cumulative sum of link weights along the active path ($\sum w_i$). In real protocols like OSPF,
                  weights are inversely proportional to link bandwidth (cost = reference bandwidth / interface bandwidth).
                </p>
              </div>

              <div style={{ background: '#080c14', padding: 16, borderRadius: 10, border: '1px solid #1e2c40' }}>
                <div style={{ fontWeight: 700, color: '#38bdf8', fontSize: '0.9rem', marginBottom: 6 }}>
                  🔀 Hop Count
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                  The number of router-to-router forwarding steps across the topology. Calculated as the total number
                  of routers in the path minus 1 (e.g., $A \to B \to D \to F \to H$ is 4 hops).
                </p>
              </div>

              <div style={{ background: '#080c14', padding: 16, borderRadius: 10, border: '1px solid #1e2c40' }}>
                <div style={{ fontWeight: 700, color: '#f59e0b', fontSize: '0.9rem', marginBottom: 6 }}>
                  ⏱️ Convergence Latency (Recovery Time)
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                  The wall-clock duration in seconds measured from failure detection to Dijkstra alternative path
                  recalculation. Note: This measures simulation execution latency, not physical hardware convergence.
                </p>
              </div>

              <div style={{ background: '#080c14', padding: 16, borderRadius: 10, border: '1px solid #1e2c40' }}>
                <div style={{ fontWeight: 700, color: '#f43f5e', fontSize: '0.9rem', marginBottom: 6 }}>
                  📦 Packet Loss Simulation
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                  Virtual packets forwarded along a path verify node and link operational state at every hop. If a link
                  is severed or router is offline, the packet is immediately dropped and registered as lost.
                </p>
              </div>

              <div style={{ background: '#080c14', padding: 16, borderRadius: 10, border: '1px solid #1e2c40' }}>
                <div style={{ fontWeight: 700, color: '#a855f7', fontSize: '0.9rem', marginBottom: 6 }}>
                  🛡️ Client Trust Score
                </div>
                <p style={{ fontSize: '0.8rem', color: '#cbd5e1', lineHeight: 1.5, margin: 0 }}>
                  Dynamic reputation score (0–100) assigned to each client. Authorized requests maintain 100;
                  unauthorized proposals (loops, nonexistent nodes, invalid destinations) incur heavy policy penalties.
                </p>
              </div>
            </div>

            <div style={{ marginTop: 20, textAlign: 'right' }}>
              <button className="btn-primary" style={{ width: 'auto' }} onClick={() => setIsOpen(false)}>
                Got it, Back to Dashboard
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
