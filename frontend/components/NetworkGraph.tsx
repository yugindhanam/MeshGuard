'use client';
import React, { useRef, useEffect, useCallback, useState } from 'react';
import type { NodeData, LinkData } from '@/lib/types';

interface Props {
  nodes: NodeData[];
  links: LinkData[];
  currentRoute: string[] | null;
  width?: number;
  height?: number;
}

const NODE_RADIUS = 26;
const COLORS = {
  active: '#10b981',
  activeBorder: '#34d399',
  failed: '#f43f5e',
  failedBorder: '#fda4af',
  route: '#00e5ff',
  routeBorder: '#ffffff',
  database: '#a855f7',
  databaseBorder: '#c084fc',
  linkActive: '#334155',
  linkRoute: '#00e5ff',
  linkFailed: '#f43f5e',
  bg: '#0b0f19',
};

interface HoverInfo {
  id: string;
  label: string;
  status: string;
  incidentLinks: { target: string; cost: number; active: boolean }[];
  x: number;
  y: number;
}

export default function NetworkGraph({ nodes, links, currentRoute, width = 1200, height = 440 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const packetRef = useRef({ segIdx: 0, t: 0, trail: [] as { x: number; y: number }[] });
  const [hoveredNode, setHoveredNode] = useState<HoverInfo | null>(null);

  // Map node id -> canvas coords (scaled from topology coords)
  const getPositions = useCallback(() => {
    if (!nodes.length) return new Map<string, { x: number; y: number }>();
    const xs = nodes.map((n) => n.x);
    const ys = nodes.map((n) => n.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const padX = 80;
    const padY = 60;
    const scaleX = (width - padX * 2) / (maxX - minX || 1);
    const scaleY = (height - padY * 2) / (maxY - minY || 1);
    const scale = Math.min(scaleX, scaleY);
    const offX = (width - (maxX - minX) * scale) / 2 - minX * scale;
    const offY = (height - (maxY - minY) * scale) / 2 - minY * scale;
    const map = new Map<string, { x: number; y: number }>();
    nodes.forEach((n) => map.set(n.id, { x: n.x * scale + offX, y: n.y * scale + offY }));
    return map;
  }, [nodes, width, height]);

  const routeSet = new Set(currentRoute || []);
  const routeEdges = new Set<string>();
  if (currentRoute && currentRoute.length > 1) {
    for (let i = 0; i < currentRoute.length - 1; i++) {
      const a = currentRoute[i], b = currentRoute[i + 1];
      routeEdges.add(`${a}-${b}`);
      routeEdges.add(`${b}-${a}`);
    }
  }

  // Handle canvas mouse move for interactive node inspection
  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = width / rect.width;
    const scaleY = height / rect.height;
    const mouseX = (e.clientX - rect.left) * scaleX;
    const mouseY = (e.clientY - rect.top) * scaleY;

    const pos = getPositions();
    let found: HoverInfo | null = null;

    for (const node of nodes) {
      const p = pos.get(node.id);
      if (!p) continue;
      const dist = Math.hypot(mouseX - p.x, mouseY - p.y);
      if (dist <= NODE_RADIUS + 6) {
        // Collect incident links
        const incident = links
          .filter((l) => l.source === node.id || l.target === node.id)
          .map((l) => {
            const peer = l.source === node.id ? l.target : l.source;
            const peerNode = nodes.find((n) => n.id === peer);
            const active = l.status === 'ACTIVE' && node.status === 'ACTIVE' && peerNode?.status === 'ACTIVE';
            return { target: peer, cost: l.weight, active };
          });

        found = {
          id: node.id,
          label: node.label,
          status: node.status,
          incidentLinks: incident,
          x: p.x,
          y: p.y,
        };
        break;
      }
    }
    setHoveredNode(found);
  };

  const handleMouseLeave = () => setHoveredNode(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    const pos = getPositions();
    const pkt = packetRef.current;

    // Reset packet position when route changes
    pkt.segIdx = 0;
    pkt.t = 0;
    pkt.trail = [];

    function draw() {
      ctx.clearRect(0, 0, width, height);

      // Cyber NOC Background
      ctx.fillStyle = COLORS.bg;
      ctx.fillRect(0, 0, width, height);

      // Grid background effect
      ctx.strokeStyle = 'rgba(30, 44, 64, 0.25)';
      ctx.lineWidth = 1;
      const gridSize = 40;
      for (let x = 0; x < width; x += gridSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += gridSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      // ── 1. Draw Links ──
      links.forEach((link) => {
        const from = pos.get(link.source);
        const to = pos.get(link.target);
        if (!from || !to) return;
        const key1 = `${link.source}-${link.target}`;
        const isRoute = routeEdges.has(key1);
        const isFailed = link.status === 'FAILED';
        const fromActive = nodes.find((n) => n.id === link.source)?.status === 'ACTIVE';
        const toActive = nodes.find((n) => n.id === link.target)?.status === 'ACTIVE';
        const effectiveFail = isFailed || !fromActive || !toActive;

        ctx.beginPath();
        ctx.moveTo(from.x, from.y);
        ctx.lineTo(to.x, to.y);

        if (effectiveFail) {
          // Severed link: crimson dashed line
          ctx.strokeStyle = COLORS.linkFailed;
          ctx.lineWidth = 3;
          ctx.setLineDash([8, 6]);
          ctx.shadowColor = 'rgba(244, 63, 94, 0.6)';
          ctx.shadowBlur = 6;
        } else if (isRoute) {
          // Active verified route link: glowing cyan
          ctx.strokeStyle = COLORS.linkRoute;
          ctx.lineWidth = 5;
          ctx.setLineDash([]);
          ctx.shadowColor = '#00e5ff';
          ctx.shadowBlur = 12;
        } else {
          // Standard operational link
          ctx.strokeStyle = COLORS.linkActive;
          ctx.lineWidth = 2.2;
          ctx.setLineDash([]);
          ctx.shadowBlur = 0;
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.setLineDash([]);

        // Link Badge (Weight & Status)
        const mx = (from.x + to.x) / 2;
        const my = (from.y + to.y) / 2;

        if (effectiveFail) {
          // Severed badge
          ctx.fillStyle = '#1c1015';
          ctx.strokeStyle = '#f43f5e';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.roundRect(mx - 34, my - 10, 68, 20, 4);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#f43f5e';
          ctx.font = 'bold 9px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`✖ SEVERED`, mx, my);
        } else if (isRoute) {
          // Route badge with glow
          ctx.fillStyle = '#061a29';
          ctx.strokeStyle = '#00e5ff';
          ctx.lineWidth = 1.2;
          ctx.beginPath();
          ctx.roundRect(mx - 24, my - 10, 48, 20, 4);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#00e5ff';
          ctx.font = 'bold 10px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`cost: ${link.weight}`, mx, my);
        } else {
          // Standard cost badge
          ctx.fillStyle = '#0f172a';
          ctx.strokeStyle = '#1e2c40';
          ctx.lineWidth = 1;
          ctx.beginPath();
          ctx.roundRect(mx - 15, my - 9, 30, 18, 4);
          ctx.fill();
          ctx.stroke();

          ctx.fillStyle = '#94a3b8';
          ctx.font = '600 10px monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'middle';
          ctx.fillText(`${link.weight}`, mx, my);
        }
      });

      // ── 2. Draw Nodes ──
      nodes.forEach((node) => {
        const p = pos.get(node.id);
        if (!p) return;
        const isFailed = node.status === 'FAILED';
        const isOnRoute = routeSet.has(node.id) && !isFailed;
        const isDb = node.id === 'H';

        let mainColor = COLORS.active;
        let borderColor = COLORS.activeBorder;
        let statusTag = 'ONLINE';
        let statusIcon = '✔';

        if (isFailed) {
          mainColor = COLORS.failed;
          borderColor = COLORS.failedBorder;
          statusTag = 'DOWN';
          statusIcon = '✖';
        } else if (isOnRoute) {
          mainColor = COLORS.route;
          borderColor = COLORS.routeBorder;
          statusTag = 'ROUTE';
          statusIcon = '★';
        } else if (isDb) {
          mainColor = COLORS.database;
          borderColor = COLORS.databaseBorder;
          statusTag = 'DEST';
          statusIcon = '🗄️';
        }

        // Outer Glow Halo
        ctx.beginPath();
        ctx.arc(p.x, p.y, NODE_RADIUS + 8, 0, Math.PI * 2);
        const halo = ctx.createRadialGradient(p.x, p.y, NODE_RADIUS - 4, p.x, p.y, NODE_RADIUS + 12);
        halo.addColorStop(0, mainColor + (isFailed ? '40' : isOnRoute ? '55' : '25'));
        halo.addColorStop(1, 'transparent');
        ctx.fillStyle = halo;
        ctx.fill();

        // Node Circle Body
        ctx.beginPath();
        ctx.arc(p.x, p.y, NODE_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = '#0a101d';
        ctx.fill();
        ctx.strokeStyle = mainColor;
        ctx.lineWidth = isOnRoute ? 3.5 : 2.5;
        ctx.shadowColor = mainColor;
        ctx.shadowBlur = isOnRoute ? 18 : isFailed ? 12 : 6;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Node Inner Core
        ctx.beginPath();
        ctx.arc(p.x, p.y, NODE_RADIUS - 5, 0, Math.PI * 2);
        ctx.fillStyle = mainColor + '18';
        ctx.fill();

        // Node Router ID Label
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 14px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.id, p.x, p.y - 4);

        // Status Tag + Icon below router ID
        ctx.font = 'bold 8.5px monospace';
        ctx.fillStyle = mainColor;
        ctx.fillText(`${statusIcon} ${statusTag}`, p.x, p.y + 11);

        // Subtitle (Database marker for H, or Router label)
        ctx.font = '600 9.5px sans-serif';
        ctx.fillStyle = isDb ? '#c084fc' : '#94a3b8';
        ctx.fillText(isDb ? 'Database (H)' : `Router ${node.id}`, p.x, p.y + NODE_RADIUS + 13);
      });

      // ── 3. Draw Traveling Packet Animation along Active Route ──
      if (currentRoute && currentRoute.length > 1) {
        const pkt = packetRef.current;
        const route = currentRoute;
        const fromId = route[pkt.segIdx];
        const toId = route[pkt.segIdx + 1];
        const p0 = pos.get(fromId);
        const p1 = pos.get(toId);

        if (p0 && p1) {
          const hx = p0.x + (p1.x - p0.x) * pkt.t;
          const hy = p0.y + (p1.y - p0.y) * pkt.t;

          pkt.trail.push({ x: hx, y: hy });
          if (pkt.trail.length > 40) pkt.trail.shift();

          // Draw fading tail
          pkt.trail.forEach((pt, i) => {
            const frac = i / pkt.trail.length;
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 1.8 + frac * 3.2, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0, 229, 255, ${frac * 0.55})`;
            ctx.fill();
          });

          // Radial glow halo around packet head
          const halo = ctx.createRadialGradient(hx, hy, 0, hx, hy, 22);
          halo.addColorStop(0, 'rgba(0, 229, 255, 0.45)');
          halo.addColorStop(1, 'transparent');
          ctx.beginPath();
          ctx.arc(hx, hy, 22, 0, Math.PI * 2);
          ctx.fillStyle = halo;
          ctx.fill();

          // Packet core
          ctx.beginPath();
          ctx.arc(hx, hy, 6, 0, Math.PI * 2);
          ctx.fillStyle = '#ffffff';
          ctx.shadowColor = '#00e5ff';
          ctx.shadowBlur = 18;
          ctx.fill();
          ctx.shadowBlur = 0;

          // Packet forwarding speed
          pkt.t += 0.012;
          if (pkt.t >= 1) {
            pkt.t = 0;
            pkt.trail = [];
            pkt.segIdx = (pkt.segIdx + 1) % (route.length - 1);
          }
        }
      }

      animRef.current = requestAnimationFrame(draw);
    }

    animRef.current = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(animRef.current);
  }, [nodes, links, currentRoute, width, height, getPositions, routeSet, routeEdges]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <canvas
        ref={canvasRef}
        width={width}
        height={height}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        style={{
          width: '100%',
          height: '100%',
          display: 'block',
          cursor: hoveredNode ? 'pointer' : 'default',
        }}
      />

      {/* Interactive Router Inspector Hover Card */}
      {hoveredNode && (
        <div
          style={{
            position: 'absolute',
            left: Math.min(hoveredNode.x + 20, width - 240),
            top: Math.max(10, hoveredNode.y - 60),
            zIndex: 30,
            background: 'rgba(15, 23, 42, 0.95)',
            border: `1px solid ${hoveredNode.status === 'ACTIVE' ? '#10b981' : '#f43f5e'}`,
            borderRadius: 8,
            padding: '10px 14px',
            color: '#f8fafc',
            fontSize: '0.75rem',
            boxShadow: '0 10px 25px rgba(0,0,0,0.6)',
            pointerEvents: 'none',
            minWidth: 200,
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
            <strong style={{ fontSize: '0.85rem' }}>Router {hoveredNode.id}</strong>
            <span
              style={{
                fontSize: '0.68rem',
                fontWeight: 700,
                color: hoveredNode.status === 'ACTIVE' ? '#10b981' : '#f43f5e',
              }}
            >
              {hoveredNode.status === 'ACTIVE' ? '● ONLINE' : '✖ OFFLINE'}
            </span>
          </div>
          <div style={{ fontSize: '0.7rem', color: '#94a3b8', marginBottom: 6 }}>
            {hoveredNode.id === 'H' ? 'Primary Destination (Database)' : 'Core Transit Router'}
          </div>
          <div style={{ borderTop: '1px solid #1e2c40', paddingTop: 4, marginTop: 4 }}>
            <span style={{ fontSize: '0.68rem', color: '#64748b', textTransform: 'uppercase' }}>Connected Links:</span>
            <div style={{ marginTop: 2, display: 'flex', flexWrap: 'wrap', gap: 4 }}>
              {hoveredNode.incidentLinks.map((l) => (
                <span
                  key={l.target}
                  style={{
                    background: '#080c14',
                    border: `1px solid ${l.active ? '#334155' : '#f43f5e'}`,
                    padding: '2px 6px',
                    borderRadius: 4,
                    fontSize: '0.68rem',
                    color: l.active ? '#94a3b8' : '#f43f5e',
                  }}
                >
                  {l.target} (cost {l.cost}) {l.active ? '✔' : '✖'}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
