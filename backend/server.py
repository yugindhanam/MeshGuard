"""
server.py – MeshGuard FastAPI Backend
Exposes all Python simulation logic as REST endpoints consumed by the Next.js frontend.
"""

import datetime
import sys
import os

# Make the MeshGuard Python modules importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from network.manager import NetworkManager
from network.topology import normalize_edge
from routing.dijkstra import find_shortest_path
from simulation.packet import PacketSimulator
from healing.self_healing import SelfHealingEngine
from monitoring.failure_detector import FailureDetector
from security.monitor import SecurityMonitor

# ─── Singleton state (lives for the lifetime of the process) ─────────────────
manager = NetworkManager()
packet_sim = PacketSimulator()
security_monitor = SecurityMonitor(manager, packet_sim)

event_logs: list[dict] = []
current_route: Optional[list] = None
current_cost: Optional[float] = None
route_hops: list = []
last_healing_event: Optional[dict] = None
last_recovery_time: Optional[float] = None
packet_logs: list = []
source_router: str = "A"
dest_router: str = "H"


def log_event(message: str) -> None:
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    event_logs.append({"timestamp": timestamp, "message": message})
    if len(event_logs) > 300:
        event_logs.pop(0)
    security_monitor.event_sink = log_event  # keep wired


security_monitor.event_sink = log_event

# ─── FastAPI app ─────────────────────────────────────────────────────────────
app = FastAPI(title="MeshGuard API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request models ──────────────────────────────────────────────────────────
class RouteRequest(BaseModel):
    source: str
    destination: str


class FailLinkRequest(BaseModel):
    u: str
    v: str


class FailNodeRequest(BaseModel):
    node: str


class AttackRequest(BaseModel):
    client_id: str


class DatabaseRequest(BaseModel):
    client_id: str
    proposed_path: Optional[List[str]] = None


# ─── Helpers ─────────────────────────────────────────────────────────────────
def serialise_client(c):
    return {
        "client_id": c.client_id,
        "source": c.source,
        "destination": c.destination,
        "route": c.route,
        "status": c.status,
        "trust_score": c.trust_score,
        "route_changes": c.route_changes,
        "blocked_requests": c.blocked_requests,
        "delivered": c.delivered,
        "last_request": c.last_request,
        "last_incident": c.last_incident,
        "expected_route": c.expected_route,
    }


def get_topology_payload():
    """Full topology snapshot sent to the frontend graph renderer."""
    nodes = []
    for node_id in manager.base_graph.nodes:
        data = manager.base_graph.nodes[node_id]
        nodes.append({
            "id": node_id,
            "label": data.get("label", node_id),
            "x": data.get("x", 0),
            "y": data.get("y", 0),
            "status": manager.node_status.get(node_id, "ACTIVE"),
        })

    links = []
    for u, v, data in manager.base_graph.edges(data=True):
        edge_key = normalize_edge(u, v)
        links.append({
            "source": u,
            "target": v,
            "weight": data.get("weight", 1),
            "status": manager.link_status.get(edge_key, "ACTIVE"),
        })

    health = FailureDetector.evaluate_network_health(manager, source_router, dest_router)

    return {
        "nodes": nodes,
        "links": links,
        "stats": manager.get_statistics(),
        "packet_stats": packet_sim.get_stats(),
        "health": {
            "status": health["status"],
            "badge": health["badge"],
            "is_reachable": health["is_reachable"],
            "reason": health["reason"],
            "failed_nodes": health["failed_nodes"],
            "failed_links": [[e[0], e[1]] for e in health["failed_links"]],
        },
        "current_route": current_route,
        "current_cost": current_cost,
        "route_hops": route_hops,
        "last_healing_event": last_healing_event,
        "last_recovery_time": last_recovery_time,
        "packet_logs": packet_logs,
        "source_router": source_router,
        "dest_router": dest_router,
        "clients": {cid: serialise_client(c) for cid, c in security_monitor.clients.items()},
        "event_logs": event_logs[-100:],
    }


# ─── Endpoints ───────────────────────────────────────────────────────────────
@app.get("/api/topology")
def get_topology():
    security_monitor.refresh_routes()
    return get_topology_payload()


@app.post("/api/route/find")
def find_route(body: RouteRequest):
    global current_route, current_cost, route_hops, source_router, dest_router, last_healing_event
    source_router = body.source
    dest_router = body.destination

    if body.source == body.destination:
        raise HTTPException(400, "Source and destination cannot be identical")
    if not manager.is_node_active(body.source):
        raise HTTPException(400, f"Source Router {body.source} is OFFLINE")
    if not manager.is_node_active(body.destination):
        raise HTTPException(400, f"Destination Router {body.destination} is OFFLINE")

    active_g = manager.get_active_graph()
    path, cost, hops = find_shortest_path(active_g, body.source, body.destination)

    if path:
        current_route = path
        current_cost = cost
        route_hops = hops
        last_healing_event = None
        route_str = " → ".join(path)
        log_event(f"[ROUTE] Optimal path computed: {route_str} (Cost: {cost})")
        return {"path": path, "cost": cost, "hops": hops, "topology": get_topology_payload()}
    else:
        current_route = None
        current_cost = None
        route_hops = []
        log_event(f"[ROUTE] No path between {body.source} and {body.destination}")
        raise HTTPException(404, "No route exists between the selected routers")


@app.post("/api/packet/transmit")
def transmit_packet():
    global packet_logs
    if not current_route:
        raise HTTPException(400, "No active route. Compute a route first.")
    result = packet_sim.transmit_packet(current_route, manager)
    packet_logs = result["hop_logs"]
    for msg in result["hop_logs"]:
        log_event(f"[PACKET] {msg}")
    return {**result, "topology": get_topology_payload()}


@app.post("/api/fail/link")
def fail_link(body: FailLinkRequest):
    global current_route, current_cost, route_hops, last_healing_event, last_recovery_time
    if not manager.fail_link(body.u, body.v):
        raise HTTPException(400, f"Link {body.u}-{body.v} not found or already failed")
    log_event(f"[FAIL] Link {body.u}-{body.v} severed")
    log_event(f"[MONITOR] Failure detected: Link {body.u} <-> {body.v}")

    if current_route:
        log_event("[HEAL] MeshGuard initiating autonomous reroute...")
        result = SelfHealingEngine.trigger_healing(
            manager=manager,
            source=source_router,
            destination=dest_router,
            current_path=current_route,
            failure_type="Link",
            failed_item=f"{body.u}-{body.v}",
        )
        last_healing_event = {
            **result,
            "recovered_cost": result["recovered_cost"] if result["recovered_cost"] != float("inf") else None,
        }
        last_recovery_time = result["recovery_time"]
        if result["status"] == "RECOVERED":
            current_route = result["recovered_path"]
            current_cost = result["recovered_cost"]
            route_hops = result["hops_detail"]
            log_event(f"[HEAL] Alternative route: {' → '.join(result['recovered_path'])}")
            log_event(f"[HEAL] Recovered in {result['recovery_time']:.3f}s")
        elif result["status"] == "FAILED_NO_PATH":
            current_route = None
            current_cost = None
            route_hops = []
            log_event("[FAIL] Network partitioned – no alternative path.")

    security_monitor.refresh_routes()
    return get_topology_payload()


@app.post("/api/fail/node")
def fail_node(body: FailNodeRequest):
    global current_route, current_cost, route_hops, last_healing_event, last_recovery_time
    if not manager.fail_node(body.node):
        raise HTTPException(400, f"Router {body.node} not found or already failed")
    log_event(f"[FAIL] Router {body.node} crashed")

    if current_route:
        log_event("[HEAL] MeshGuard initiating autonomous reroute...")
        result = SelfHealingEngine.trigger_healing(
            manager=manager,
            source=source_router,
            destination=dest_router,
            current_path=current_route,
            failure_type="Router",
            failed_item=body.node,
        )
        last_healing_event = {
            **result,
            "recovered_cost": result["recovered_cost"] if result["recovered_cost"] != float("inf") else None,
        }
        last_recovery_time = result["recovery_time"]
        if result["status"] == "RECOVERED":
            current_route = result["recovered_path"]
            current_cost = result["recovered_cost"]
            route_hops = result["hops_detail"]
            log_event(f"[HEAL] Alternative route: {' → '.join(result['recovered_path'])}")
        elif result["status"] == "FAILED_NO_PATH":
            current_route = None
            current_cost = None
            route_hops = []
            log_event("[FAIL] Network partitioned.")

    security_monitor.refresh_routes()
    return get_topology_payload()


@app.post("/api/restore/link")
def restore_link(body: FailLinkRequest):
    global current_route, current_cost, route_hops
    if not manager.restore_link(body.u, body.v):
        raise HTTPException(400, f"Link {body.u}-{body.v} not found or already active")
    log_event(f"[RESTORE] Link {body.u}-{body.v} restored")
    security_monitor.refresh_routes()

    if manager.is_node_active(source_router) and manager.is_node_active(dest_router):
        act_g = manager.get_active_graph()
        p, c, h = find_shortest_path(act_g, source_router, dest_router)
        if p:
            current_route = p
            current_cost = c
            route_hops = h
            log_event(f"[ROUTE] Route updated: {' → '.join(p)} (Cost: {c})")
    return get_topology_payload()


@app.post("/api/restore/node")
def restore_node(body: FailNodeRequest):
    global current_route, current_cost, route_hops
    if not manager.restore_node(body.node):
        raise HTTPException(400, f"Router {body.node} not found or already active")
    log_event(f"[RESTORE] Router {body.node} powered up")
    security_monitor.refresh_routes()

    if manager.is_node_active(source_router) and manager.is_node_active(dest_router):
        act_g = manager.get_active_graph()
        p, c, h = find_shortest_path(act_g, source_router, dest_router)
        if p:
            current_route = p
            current_cost = c
            route_hops = h
            log_event(f"[ROUTE] Route updated: {' → '.join(p)} (Cost: {c})")
    return get_topology_payload()


@app.post("/api/reset")
def reset_network():
    global current_route, current_cost, route_hops, last_healing_event, last_recovery_time, packet_logs
    manager.reset_network()
    packet_sim.reset_metrics()
    current_route = None
    current_cost = None
    route_hops = []
    last_healing_event = None
    last_recovery_time = None
    packet_logs = []
    # Re-init security monitor
    import importlib
    from security.monitor import SecurityMonitor as SM
    global security_monitor
    security_monitor = SM(manager, packet_sim, event_sink=log_event)
    log_event("[RESET] Network topology reset to default state")
    return get_topology_payload()


@app.post("/api/security/request")
def security_request(body: DatabaseRequest):
    security_monitor.refresh_routes()
    result = security_monitor.request_database(body.client_id, body.proposed_path)
    return {**result, "topology": get_topology_payload()}


@app.post("/api/security/attack")
def simulate_attack(body: AttackRequest):
    result = security_monitor.simulate_attack(body.client_id)
    return {**result, "topology": get_topology_payload()}


@app.get("/api/logs")
def get_logs():
    return {"logs": event_logs[-100:]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
