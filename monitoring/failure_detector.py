"""
failure_detector.py - Network Monitoring and Failure Detection
Monitors network element states, checks path integrity, and determines network health status.
"""

from typing import Dict, List, Optional, Tuple, Any
import networkx as nx
from network.manager import NetworkManager
from network.topology import normalize_edge


class FailureDetector:
    """
    Simulated network monitor: checks router heartbeats, link connectivity,
    and detects whether active routing paths have been compromised.
    """

    HEALTH_HEALTHY = "HEALTHY"
    HEALTH_DEGRADED = "DEGRADED / RECOVERED"
    HEALTH_DISCONNECTED = "NETWORK DISCONNECTED"

    @staticmethod
    def is_path_compromised(
        path: Optional[List[str]],
        failed_nodes: List[str],
        failed_links: List[Tuple[str, str]]
    ) -> Tuple[bool, List[str]]:
        """
        Checks whether the given path traverses any failed node or failed link.
        Returns (is_compromised, reasons).
        """
        if not path or len(path) < 2:
            return False, []

        compromised = False
        reasons = []
        failed_nodes_set = set(failed_nodes)
        failed_links_set = set(failed_links)

        # Check nodes in path
        for node in path:
            if node in failed_nodes_set:
                compromised = True
                reasons.append(f"Router {node} is FAILED")

        # Check links in path
        for i in range(len(path) - 1):
            edge = normalize_edge(path[i], path[i + 1])
            if edge in failed_links_set:
                compromised = True
                reasons.append(f"Link {edge[0]} <-> {edge[1]} is FAILED")

        return compromised, reasons

    @classmethod
    def evaluate_network_health(
        cls,
        manager: NetworkManager,
        source: Optional[str] = None,
        destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Evaluates overall network health and reachability between source and destination.
        """
        failed_nodes = manager.get_failed_nodes()
        failed_links = manager.get_failed_links()
        active_graph = manager.get_active_graph()

        has_failures = bool(failed_nodes or failed_links)

        # Reachability test if source and destination provided
        is_reachable = True
        reachability_reason = "Normal connectivity"

        if source and destination:
            if not manager.is_node_active(source):
                is_reachable = False
                reachability_reason = f"Source Router {source} is down"
            elif not manager.is_node_active(destination):
                is_reachable = False
                reachability_reason = f"Destination Router {destination} is down"
            else:
                try:
                    is_reachable = nx.has_path(active_graph, source, destination)
                    if not is_reachable:
                        reachability_reason = f"No viable path exists between {source} and {destination}"
                except Exception:
                    is_reachable = False
                    reachability_reason = "Path evaluation error"

        # Determine overall status
        if not is_reachable:
            status = cls.HEALTH_DISCONNECTED
            badge = "🔴 NETWORK DISCONNECTED"
            color = "#dc3545"
        elif has_failures:
            status = cls.HEALTH_DEGRADED
            badge = "🟡 RECOVERED / DEGRADED"
            color = "#ffc107"
        else:
            status = cls.HEALTH_HEALTHY
            badge = "🟢 HEALTHY"
            color = "#28a745"

        return {
            "status": status,
            "badge": badge,
            "color": color,
            "has_failures": has_failures,
            "is_reachable": is_reachable,
            "reason": reachability_reason,
            "failed_nodes": failed_nodes,
            "failed_links": failed_links
        }
