export const API = 'http://localhost:8000';

export async function apiFetch(path: string, opts?: RequestInit) {
  const res = await fetch(`${API}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'API error');
  }
  return res.json();
}

export const getTopology = () => apiFetch('/api/topology');
export const findRoute = (source: string, destination: string) =>
  apiFetch('/api/route/find', { method: 'POST', body: JSON.stringify({ source, destination }) });
export const transmitPacket = () =>
  apiFetch('/api/packet/transmit', { method: 'POST' });
export const failLink = (u: string, v: string) =>
  apiFetch('/api/fail/link', { method: 'POST', body: JSON.stringify({ u, v }) });
export const failNode = (node: string) =>
  apiFetch('/api/fail/node', { method: 'POST', body: JSON.stringify({ node }) });
export const restoreLink = (u: string, v: string) =>
  apiFetch('/api/restore/link', { method: 'POST', body: JSON.stringify({ u, v }) });
export const restoreNode = (node: string) =>
  apiFetch('/api/restore/node', { method: 'POST', body: JSON.stringify({ node }) });
export const resetNetwork = () =>
  apiFetch('/api/reset', { method: 'POST' });
export const securityRequest = (client_id: string, proposed_path?: string[]) =>
  apiFetch('/api/security/request', { method: 'POST', body: JSON.stringify({ client_id, proposed_path }) });
export const simulateAttack = (client_id: string) =>
  apiFetch('/api/security/attack', { method: 'POST', body: JSON.stringify({ client_id }) });
