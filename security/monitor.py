"""Client request gate, event history and recovery through the shared healing engine."""

import datetime
from typing import Callable, Dict, List, Optional
import networkx as nx

from healing.self_healing import SelfHealingEngine
from network.manager import NetworkManager
from simulation.packet import PacketSimulator
from .attack_simulator import unauthorized_route
from .threat_detector import ClientState, SecurityPolicy, ThreatDetector


class SecurityMonitor:
    def __init__(self, manager: NetworkManager, packet_sim: PacketSimulator,
                 policy: Optional[SecurityPolicy] = None,
                 event_sink: Optional[Callable[[str], None]] = None):
        self.manager = manager
        self.packet_sim = packet_sim
        self.detector = ThreatDetector(policy)
        self.event_sink = event_sink
        self.events: List[dict] = []
        self.clients: Dict[str, ClientState] = {
            f"Client {i}": ClientState(f"Client {i}") for i in range(1, 4)
        }
        for client in self.clients.values():
            self._recover(client, ["Initial database connection"], initial=True)

    def _log(self, client: ClientState, message: str) -> None:
        self.events.append({"time": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
                            "client": client.client_id, "message": message})
        self.events = self.events[-300:]
        if self.event_sink:
            self.event_sink(f"[SECURITY] {client.client_id}: {message}")

    def _recover(self, client: ClientState, reasons: List[str], initial: bool = False) -> bool:
        self._log(client, "Dijkstra recalculation started on active authorized nodes")
        result = SelfHealingEngine.trigger_healing(
            self.manager, client.source, client.destination, client.expected_route,
            "Route validation", client.client_id,
            allowed_nodes=self.detector.authorized_nodes(self.manager, client),
            validation_reasons=reasons,
        )
        path = result["recovered_path"]
        if path and self.detector.validate(self.manager, client, path, check_change=False).valid:
            client.route = list(path)
            client.expected_route = list(path)
            client.status = "NORMAL" if initial else "RECOVERED"
            self._log(client, f"{client.status}: Safe route found: {' -> '.join(path)}")
            return True
        client.route = None
        client.expected_route = None
        client.status = "ISOLATED"
        self._log(client, "ISOLATED: No active trusted path; database requests blocked")
        return False

    def refresh_routes(self) -> None:
        """Reconcile equipment/trust changes without penalizing infrastructure reroutes."""
        for client in self.clients.values():
            if client.route is None:
                # Avoid duplicate recovery logs on every Streamlit rerun while disconnected.
                allowed = self.detector.authorized_nodes(self.manager, client)
                graph = self.manager.get_active_graph().subgraph(allowed)
                if client.source in graph and client.destination in graph and nx.has_path(
                    graph, client.source, client.destination
                ):
                    self._recover(client, ["Connectivity restored"])
            else:
                # Only infrastructure changes to our approved baseline are auto-healed here.
                # A client-mutated route must still reach request-time threat detection.
                result = self.detector.validate(self.manager, client, client.expected_route,
                                                check_change=False)
                if not result.valid:
                    self._recover(client, result.reasons)

    def request_database(self, client_id: str, proposed_path: Optional[List[str]] = None) -> dict:
        """Validate before forwarding; a blocked proposal never enters PacketSimulator."""
        if client_id not in self.clients:
            raise ValueError(f"Unknown client: {client_id}")
        client = self.clients[client_id]
        # Heal physical failures first only when using the server-managed route.
        if proposed_path is None:
            self.refresh_routes()
        path = client.route if proposed_path is None else proposed_path
        if path is None:
            client.last_request = "Blocked: no safe route"
            self._log(client, client.last_request)
            return {"success": False, "blocked": True, "reason": client.last_request}
        result = self.detector.validate(self.manager, client, path)
        blocked = not result.valid
        incident = None
        if blocked:
            client.blocked_requests += 1
            if result.status != "UNAVAILABLE":
                client.status = "SUSPICIOUS"
                self._log(client, "SUSPICIOUS: Abnormal route proposal detected")
                client.route_changes += int(result.changed)
                client.trust_score = max(0, client.trust_score - result.penalty)
                client.status = result.status
            self._log(client, f"{result.status}: {'; '.join(result.reasons)}")
            self._log(client, "Invalid route blocked before packet forwarding")
            incident = {"previous_path": list(client.expected_route or []),
                        "invalid_path": [str(node) for node in path]
                        if isinstance(path, (list, tuple)) else [],
                        "classification": result.status, "reasons": result.reasons,
                        "blocked": True, "safe_path": None, "delivered": False}
            client.last_incident = incident
            if not self._recover(client, result.reasons):
                client.last_request = "Blocked: no safe route"
                return {"success": False, "blocked": True, "reason": client.last_request}
            incident["safe_path"] = list(client.route)
        else:
            client.route = list(path)

        # Revalidate the selected route immediately before using the existing packet engine.
        final_check = self.detector.validate(self.manager, client, client.route)
        if not final_check.valid:
            client.route = None
            client.status = "ISOLATED"
            client.last_request = "Blocked: final route validation failed"
            return {"success": False, "blocked": True, "reason": client.last_request}
        transmission = self.packet_sim.transmit_packet(client.route, self.manager)
        client.last_request = "Database reached" if transmission["success"] else "Delivery failed"
        client.delivered += int(transmission["success"])
        if incident:
            incident["delivered"] = transmission["success"]
        self._log(client, client.last_request)
        for message in transmission["hop_logs"]:
            self._log(client, message)
        return {**transmission, "blocked": blocked}

    def simulate_attack(self, client_id: str) -> dict:
        if client_id not in self.clients:
            raise ValueError(f"Unknown client: {client_id}")
        client = self.clients[client_id]
        return self.request_database(client_id, unauthorized_route(self.manager, client))
