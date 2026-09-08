"""
topology.py - Network Topology Loader and Graph Builder
Defines and loads the router nodes and weighted links for MeshGuard.
"""

import json
import os
from typing import Dict, Any, List, Tuple
import networkx as nx

DEFAULT_TOPOLOGY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "topology.json"
)

# Fallback in-memory topology definition
FALLBACK_TOPOLOGY: Dict[str, Any] = {
    "routers": [
        {"id": "A", "label": "Router A", "x": -350, "y": 80},
        {"id": "B", "label": "Router B", "x": -150, "y": 140},
        {"id": "C", "label": "Router C", "x": -220, "y": -120},
        {"id": "D", "label": "Router D", "x": 100, "y": 140},
        {"id": "E", "label": "Router E", "x": 40, "y": -100},
        {"id": "F", "label": "Router F", "x": 280, "y": 100},
        {"id": "G", "label": "Router G", "x": 220, "y": -120},
        {"id": "H", "label": "Router H", "x": 420, "y": 0}
    ],
    "links": [
        {"source": "A", "target": "B", "weight": 2},
        {"source": "A", "target": "C", "weight": 4},
        {"source": "B", "target": "C", "weight": 3},
        {"source": "B", "target": "D", "weight": 3},
        {"source": "C", "target": "D", "weight": 4},
        {"source": "C", "target": "E", "weight": 3},
        {"source": "D", "target": "E", "weight": 2},
        {"source": "D", "target": "F", "weight": 3},
        {"source": "E", "target": "F", "weight": 3},
        {"source": "E", "target": "G", "weight": 2},
        {"source": "F", "target": "H", "weight": 2},
        {"source": "G", "target": "H", "weight": 4},
        {"source": "D", "target": "H", "weight": 6}
    ]
}


def normalize_edge(u: str, v: str) -> Tuple[str, str]:
    """Returns a canonical tuple representation for an undirected edge."""
    return (u, v) if u <= v else (v, u)


def load_topology_data(filepath: str = DEFAULT_TOPOLOGY_PATH) -> Dict[str, Any]:
    """Loads topology definitions from JSON, falling back to built-in if file is missing."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return FALLBACK_TOPOLOGY
    return FALLBACK_TOPOLOGY


def create_base_graph(topology_data: Dict[str, Any] = None) -> nx.Graph:
    """Creates and returns a NetworkX Graph populated with routers and links."""
    if topology_data is None:
        topology_data = load_topology_data()

    G = nx.Graph()

    for router in topology_data.get("routers", []):
        G.add_node(
            router["id"],
            label=router.get("label", f"Router {router['id']}"),
            x=router.get("x", 0),
            y=router.get("y", 0)
        )

    for link in topology_data.get("links", []):
        u, v = link["source"], link["target"]
        weight = link.get("weight", 1)
        G.add_edge(u, v, weight=weight)

    return G

