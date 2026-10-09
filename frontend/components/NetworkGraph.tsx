'use client';
import React, { useRef, useEffect, useCallback } from 'react';
import type { NodeData, LinkData } from '@/lib/types';

interface Props {
  nodes: NodeData[];
  links: LinkData[];
  currentRoute: string[] | null;
  width?: number;
  height?: number;
}

const NODE_RADIUS = 22;
const COLORS = {
  active: '#10b981',
  failed: '#f43f5e',
  route: '#00e5ff',
  linkActive: '#334155',
  linkRoute: '#00e5ff',
  linkFailed: '#f43f5e',
  bg: '#0b0f19',
};

export default function NetworkGraph({ nodes, links, currentRoute, width = 900, height = 440 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const animRef = useRef<number>(0);
  const packetRef = useRef({ segIdx: 0, t: 0, trail: [] as { x: number; y: number }[] });

  // Map node id -> canvas coords (scaled from topology coords)
  const getPositions = useCallback(() => {
    if (!nodes.length) return new Map<string, { x: number; y: number }>();
    const xs = nodes.map((n) => n.x);
    const ys = nodes.map((n) => n.y);
    const minX = Math.min(...xs), maxX = Math.max(...xs);
    const minY = Math.min(...ys), maxY = Math.max(...ys);
    const pad = 60;
    const scaleX = (width - pad * 2) / (maxX - minX || 1);
    const scaleY = (height - pad * 2) / (maxY - minY || 1);
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

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d')!;
    const pos = getPositions();
    const pkt = packetRef.current;
    // Reset packet when route changes
    pkt.segIdx = 0;
    pkt.t = 0;
    pkt.trail = [];

    function draw() {
      ctx.clearRect(0, 0, width, height);

      // Background
      ctx.fillStyle = COLORS.bg;
      ctx.fillRect(0, 0, width, height);

      // Draw links
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
          ctx.strokeStyle = COLORS.linkFailed;
          ctx.lineWidth = 2;
          ctx.setLineDash([8, 6]);
        } else if (isRoute) {
          ctx.strokeStyle = COLORS.linkRoute;
          ctx.lineWidth = 4;
          ctx.setLineDash([]);
          ctx.shadowColor = '#00e5ff';
          ctx.shadowBlur = 10;
        } else {
          ctx.strokeStyle = COLORS.linkActive;
          ctx.lineWidth = 1.8;
          ctx.setLineDash([]);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;
        ctx.setLineDash([]);

        // Weight label
        const mx = (from.x + to.x) / 2;
        const my = (from.y + to.y) / 2;
        ctx.fillStyle = '#1e2c40';
        ctx.beginPath();
        ctx.roundRect(mx - 12, my - 9, 24, 18, 4);
        ctx.fill();
        ctx.fillStyle = effectiveFail ? '#f43f5e' : isRoute ? '#00e5ff' : '#64748b';
        ctx.font = '600 10px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(String(link.weight), mx, my);
      });

      // Draw nodes
      nodes.forEach((node) => {
        const p = pos.get(node.id);
        if (!p) return;
        const isOnRoute = routeSet.has(node.id) && node.status === 'ACTIVE';
        const color = node.status === 'FAILED' ? COLORS.failed : isOnRoute ? COLORS.route : COLORS.active;

        // Glow
        ctx.beginPath();
        ctx.arc(p.x, p.y, NODE_RADIUS + 6, 0, Math.PI * 2);
        const grd = ctx.createRadialGradient(p.x, p.y, NODE_RADIUS - 4, p.x, p.y, NODE_RADIUS + 8);
        grd.addColorStop(0, color + '44');
        grd.addColorStop(1, 'transparent');
        ctx.fillStyle = grd;
        ctx.fill();

        // Node circle
        ctx.beginPath();
        ctx.arc(p.x, p.y, NODE_RADIUS, 0, Math.PI * 2);
        ctx.fillStyle = color + '22';
        ctx.fill();
        ctx.strokeStyle = color;
        ctx.lineWidth = isOnRoute ? 3 : 2;
        ctx.shadowColor = color;
        ctx.shadowBlur = isOnRoute ? 18 : 8;
        ctx.stroke();
        ctx.shadowBlur = 0;

        // Label
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 13px monospace';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(node.id, p.x, p.y - 1);

        // Status badge
        ctx.font = '600 8px monospace';
        ctx.fillStyle = color;
        ctx.fillText(node.status === 'FAILED' ? 'DOWN' : isOnRoute ? 'ROUTE' : 'ON', p.x, p.y + 11);
      });

      // Packet animation
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
          if (pkt.trail.length > 48) pkt.trail.shift();

          // Trail
          pkt.trail.forEach((pt, i) => {
            const frac = i / pkt.trail.length;
            ctx.beginPath();
            ctx.arc(pt.x, pt.y, 1.8 + frac * 3, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(0,229,255,${frac * 0.5})`;
            ctx.fill();
          });

          // Glow halo
          const halo = ctx.createRadialGradient(hx, hy, 0, hx, hy, 20);
          halo.addColorStop(0, 'rgba(0,229,255,0.35)');
          halo.addColorStop(1, 'transparent');
          ctx.beginPath();
          ctx.arc(hx, hy, 20, 0, Math.PI * 2);
          ctx.fillStyle = halo;
          ctx.fill();

          // Dot
          ctx.beginPath();
          ctx.arc(hx, hy, 5.5, 0, Math.PI * 2);
          ctx.fillStyle = '#00e5ff';
          ctx.shadowColor = '#00e5ff';
          ctx.shadowBlur = 16;
          ctx.fill();
          ctx.shadowBlur = 0;

          pkt.t += 0.014;
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
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [nodes, links, currentRoute, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{ width: '100%', height: '100%', display: 'block', borderRadius: '10px' }}
    />
  );
}
