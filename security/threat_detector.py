"""Explainable route validation; physical outages are not malicious behaviour."""

from dataclasses import dataclass, field
from typing import List, Optional, Set

from network.manager import NetworkManager


@dataclass(frozen=True)
class SecurityPolicy:
    unauthorized_penalty: int = 40
    invalid_route_penalty: int = 40
    unexpected_route_penalty: int = 20
    repeated_change_penalty: int = 10
    repeated_change_threshold: int = 3


@dataclass
class ClientState:
    client_id: str
    source: str = "A"
    destination: str = "H"
    allowed_nodes: Optional[Set[str]] = None
    route: Optional[List[str]] = None
    status: str = "NORMAL"
    trust_score: int = 100
    route_changes: int = 0
    blocked_requests: int = 0
    delivered: int = 0
    last_request: str = "Not sent"
    last_incident: Optional[dict] = None
    expected_route: Optional[List[str]] = None


@dataclass
class ValidationResult:
    status: str
    reasons: List[str] = field(default_factory=list)
    penalty: int = 0
    changed: bool = False

    @property
    def valid(self) -> bool:
        return self.status == "NORMAL"


class ThreatDetector:
    def __init__(self, policy: Optional[SecurityPolicy] = None):
        self.policy = policy or SecurityPolicy()

    @staticmethod
    def authorized_nodes(manager: NetworkManager, client: ClientState) -> Set[str]:
        return {
            node for node, data in manager.base_graph.nodes(data=True)
            if data.get("trusted", True)
            and (client.allowed_nodes is None or node in client.allowed_nodes)
        }

    def validate(self, manager: NetworkManager, client: ClientState,
                 path: Optional[List[str]], check_change: bool = True) -> ValidationResult:
        if not isinstance(path, (list, tuple)) or not path or any(
            not isinstance(node, str) for node in path
        ):
            return ValidationResult("MALICIOUS", ["Empty or malformed route"],
                                    self.policy.invalid_route_penalty)

        graph = manager.base_graph
        reasons = []
        penalty = 0
        if path[0] != client.source or path[-1] != client.destination:
            reasons.append("Incorrect client source or database destination")
        if len(set(path)) != len(path):
            reasons.append("Routing loop detected")
        missing = [node for node in path if node not in graph]
        if missing:
            reasons.append(f"Unknown node: {', '.join(missing)}")
        if any(not graph.has_edge(u, v) for u, v in zip(path, path[1:])):
            reasons.append("Nonexistent edge / disconnected route")
        if reasons:
            penalty += self.policy.invalid_route_penalty
        unauthorized = set(path) - self.authorized_nodes(manager, client)
        if unauthorized:
            reasons.append(f"Unauthorized node: {', '.join(sorted(unauthorized))}")
            penalty += self.policy.unauthorized_penalty

        changed = bool(check_change and client.expected_route and list(path) != client.expected_route)
        malicious = bool(reasons)
        if changed:
            reasons.append("Unexpected client route change")
            penalty += self.policy.unexpected_route_penalty
            if client.route_changes + 1 >= self.policy.repeated_change_threshold:
                reasons.append("Repeated client route changes")
                penalty += self.policy.repeated_change_penalty
        if malicious:
            return ValidationResult("MALICIOUS", reasons, penalty, changed)

        # An authorized route disrupted by equipment failure is an availability issue.
        if any(not manager.is_node_active(node) for node in path) or any(
            not manager.is_link_active(u, v) for u, v in zip(path, path[1:])
        ):
            return ValidationResult("UNAVAILABLE", ["Route contains failed network equipment"])
        return ValidationResult("SUSPICIOUS" if changed else "NORMAL", reasons, penalty, changed)
