"""
manager.py - Network State Manager
Maintains the operational status of routers and links, handles failures,
restorations, and builds the active subgraph for routing.
"""

from typing import Dict, List, Tuple, Optional, Set
import networkx as nx
from .topology import create_base_graph, normalize_edge, load_topology_data


class NetworkManager:
    """
    Manages network state (nodes, links, operational statuses) and
    dynamically constructs the operational topology for MeshGuard.
    """

    STATUS_ACTIVE = "ACTIVE"
    STATUS_FAILED = "FAILED"

    def __init__(self, topology_data: Optional[Dict] = None):
        self.topology_data = topology_data or load_topology_data()
        self.base_graph = create_base_graph(self.topology_data)

        # Operational status dictionaries
        self.node_status: Dict[str, str] = {
            node: self.STATUS_ACTIVE for node in self.base_graph.nodes
        }
        self.link_status: Dict[Tuple[str, str], str] = {
            normalize_edge(u, v): self.STATUS_ACTIVE
            for u, v in self.base_graph.edges
        }

    def reset_network(self) -> None:
        """Resets all routers and links to ACTIVE status."""
        for node in self.node_status:
            self.node_status[node] = self.STATUS_ACTIVE
        for link in self.link_status:
            self.link_status[link] = self.STATUS_ACTIVE

    def fail_node(self, node_id: str) -> bool:
        """
        Marks a router as FAILED.
        Returns True if status changed, False if already failed or invalid.
        """
        if node_id not in self.node_status:
            return False
        if self.node_status[node_id] == self.STATUS_FAILED:
            return False
        self.node_status[node_id] = self.STATUS_FAILED
        return True

    def restore_node(self, node_id: str) -> bool:
        """
        Restores a router to ACTIVE.
        Returns True if status changed, False if already active or invalid.
        """
        if node_id not in self.node_status:
            return False
        if self.node_status[node_id] == self.STATUS_ACTIVE:
            return False
        self.node_status[node_id] = self.STATUS_ACTIVE
        return True

    def fail_link(self, u: str, v: str) -> bool:
        """
        Marks a network link as FAILED.
        Returns True if status changed, False if already failed or non-existent.
        """
        edge = normalize_edge(u, v)
        if edge not in self.link_status:
            return False
        if self.link_status[edge] == self.STATUS_FAILED:
            return False
        self.link_status[edge] = self.STATUS_FAILED
        return True

    def restore_link(self, u: str, v: str) -> bool:
        """
        Restores a network link to ACTIVE.
        Returns True if status changed, False if already active or non-existent.
        """
        edge = normalize_edge(u, v)
        if edge not in self.link_status:
            return False
        if self.link_status[edge] == self.STATUS_ACTIVE:
            return False
        self.link_status[edge] = self.STATUS_ACTIVE
        return True

    def is_node_active(self, node_id: str) -> bool:
        return self.node_status.get(node_id) == self.STATUS_ACTIVE

    def is_link_active(self, u: str, v: str) -> bool:
        edge = normalize_edge(u, v)
        return self.link_status.get(edge) == self.STATUS_ACTIVE

    def get_failed_nodes(self) -> List[str]:
        return sorted([n for n, s in self.node_status.items() if s == self.STATUS_FAILED])

    def get_active_nodes(self) -> List[str]:
        return sorted([n for n, s in self.node_status.items() if s == self.STATUS_ACTIVE])

    def get_failed_links(self) -> List[Tuple[str, str]]:
        return sorted([e for e, s in self.link_status.items() if s == self.STATUS_FAILED])

    def get_active_links(self) -> List[Tuple[str, str]]:
        return sorted([e for e, s in self.link_status.items() if s == self.STATUS_ACTIVE])

    def get_incident_links(self, node_id: str) -> List[Tuple[str, str]]:
        """Returns all links connected to a specific router."""
        incident = []
        for (u, v) in self.link_status:
            if u == node_id or v == node_id:
                incident.append((u, v))
        return incident

    def get_active_graph(self) -> nx.Graph:
        """
        Builds and returns a subgraph containing only active routers
        and active links between active routers.
        """
        active_G = nx.Graph()

        # Add only active nodes with attributes
        for node in self.base_graph.nodes:
            if self.is_node_active(node):
                active_G.add_node(
                    node,
                    label=self.base_graph.nodes[node].get("label", f"Router {node}"),
                    x=self.base_graph.nodes[node].get("x", 0),
                    y=self.base_graph.nodes[node].get("y", 0)
                )

        # Add only active edges where both incident nodes are active
        for u, v, data in self.base_graph.edges(data=True):
            edge = normalize_edge(u, v)
            if (
                self.is_link_active(u, v)
                and self.is_node_active(u)
                and self.is_node_active(v)
            ):
                active_G.add_edge(u, v, **data)

        return active_G

    def get_statistics(self) -> Dict[str, int]:
        """Returns current counts for network topology dashboard."""
        total_nodes = len(self.node_status)
        active_nodes = sum(1 for s in self.node_status.values() if s == self.STATUS_ACTIVE)
        failed_nodes = total_nodes - active_nodes

        total_links = len(self.link_status)
        active_links = sum(1 for s in self.link_status.values() if s == self.STATUS_ACTIVE)
        failed_links = total_links - active_links

        return {
            "total_routers": total_nodes,
            "active_routers": active_nodes,
            "failed_routers": failed_nodes,
            "total_links": total_links,
            "active_links": active_links,
            "failed_links": failed_links,
        }

