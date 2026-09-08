"""
visualizer.py - Network Topology Visualizer
Generates interactive PyVis HTML networks and high-resolution Matplotlib graphs
with dynamic node/link status coloring and route highlighting.
"""

from typing import List, Optional, Tuple, Set
import json
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
from network.manager import NetworkManager
from network.topology import normalize_edge


def get_route_edges(path: Optional[List[str]]) -> Set[Tuple[str, str]]:
    """Returns set of normalized edge tuples in the active route."""
    edges = set()
    if path and len(path) > 1:
        for i in range(len(path) - 1):
            edges.add(normalize_edge(path[i], path[i + 1]))
    return edges


def generate_pyvis_html(
    manager: NetworkManager,
    current_path: Optional[List[str]] = None,
    height: str = "480px"
) -> str:
    """
    Constructs an interactive PyVis network graph.
    - Active router: Green (#28a745)
    - Failed router: Red (#dc3545)
    - Active route nodes: Cyan/Blue (#007bff)
    - Active link: Normal gray line (#adb5bd)
    - Active route link: Bold blue highlight (#007bff, width=5)
    - Failed link: Dashed red line (#dc3545, dashes=True)
    """
    net = Network(height=height, width="100%", bgcolor="#ffffff", font_color="#212529", notebook=False)
    net.toggle_physics(False)

    route_nodes = set(current_path or [])
    route_edges = get_route_edges(current_path)

    # Add Nodes
    for node in manager.base_graph.nodes:
        is_active = manager.is_node_active(node)
        is_on_route = node in route_nodes and is_active

        # Node coordinates from topology
        x_pos = manager.base_graph.nodes[node].get("x", 0)
        # Vis.js y-axis is inverted relative to standard cartesian
        y_pos = -manager.base_graph.nodes[node].get("y", 0)

        if not is_active:
            bg_color = "#dc3545"  # Red
            border_color = "#bd2130"
            font_color = "#ffffff"
            title = f"Router {node} [STATUS: FAILED]"
            label = f"Router {node}\n(FAILED)"
        elif is_on_route:
            bg_color = "#007bff"  # Blue route highlight
            border_color = "#0056b3"
            font_color = "#ffffff"
            title = f"Router {node} [ON ACTIVE ROUTE]"
            label = f"Router {node}\n(ROUTE)"
        else:
            bg_color = "#28a745"  # Green
            border_color = "#1e7e34"
            font_color = "#ffffff"
            title = f"Router {node} [STATUS: ACTIVE]"
            label = f"Router {node}\n(ACTIVE)"

        net.add_node(
            node,
            label=label,
            title=title,
            color={
                "background": bg_color,
                "border": border_color,
                "highlight": {"background": bg_color, "border": "#000000"}
            },
            borderWidth=2,
            size=26,
            shape="dot",
            font={"color": font_color, "size": 13, "bold": True, "strokeWidth": 2, "strokeColor": "#000000"},
            x=x_pos,
            y=y_pos,
            physics=False
        )

    # Add Edges
    for u, v, data in manager.base_graph.edges(data=True):
        edge_key = normalize_edge(u, v)
        weight = data.get("weight", 1)
        link_active = manager.is_link_active(u, v)
        both_nodes_active = manager.is_node_active(u) and manager.is_node_active(v)

        is_failed = (not link_active) or (not both_nodes_active)
        is_on_route = (edge_key in route_edges) and not is_failed

        edge_label = f"c={weight}"

        if is_failed:
            edge_color = "#dc3545"
            width = 3
            dashes = [8, 8]  # Dashed line
            status_desc = "FAILED LINK" if not link_active else "INACTIVE (Router Down)"
            title = f"Link {u} <-> {v} [{status_desc}] | Cost: {weight}"
        elif is_on_route:
            edge_color = "#007bff"
            width = 5
            dashes = False
            title = f"Active Route Link {u} <-> {v} | Cost: {weight}"
        else:
            edge_color = "#6c757d"
            width = 2
            dashes = False
            title = f"Active Link {u} <-> {v} | Cost: {weight}"

        net.add_edge(
            u,
            v,
            label=edge_label,
            title=title,
            color=edge_color,
            width=width,
            dashes=dashes,
            font={"color": "#333333", "size": 12, "background": "#ffffff"}
        )

    # PyVis options for smooth display and interaction
    net.set_options("""
    var options = {
        "interaction": {
            "hover": true,
            "dragNodes": true,
            "zoomView": true,
            "navigationButtons": false
        },
        "physics": {
            "enabled": false
        }
    }
    """)

    return net.generate_html()


def generate_matplotlib_figure(
    manager: NetworkManager,
    current_path: Optional[List[str]] = None
) -> plt.Figure:
    """
    Renders high quality Matplotlib graph of network topology for fallback or export.
    """
    fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
    fig.patch.set_facecolor("#f8f9fa")
    ax.set_facecolor("#f8f9fa")

    # Positions dictionary
    pos = {
        node: (manager.base_graph.nodes[node].get("x", 0), manager.base_graph.nodes[node].get("y", 0))
        for node in manager.base_graph.nodes
    }

    route_nodes = set(current_path or [])
    route_edges = get_route_edges(current_path)

    # Classify edges
    active_edges = []
    failed_edges = []
    highlight_edges = []

    for u, v in manager.base_graph.edges():
        edge = normalize_edge(u, v)
        link_active = manager.is_link_active(u, v)
        nodes_active = manager.is_node_active(u) and manager.is_node_active(v)

        if not link_active or not nodes_active:
            failed_edges.append((u, v))
        elif edge in route_edges:
            highlight_edges.append((u, v))
        else:
            active_edges.append((u, v))

    # Draw normal active edges
    nx.draw_networkx_edges(
        manager.base_graph, pos, edgelist=active_edges,
        edge_color="#6c757d", width=2.0, ax=ax
    )

    # Draw highlighted route edges
    if highlight_edges:
        nx.draw_networkx_edges(
            manager.base_graph, pos, edgelist=highlight_edges,
            edge_color="#007bff", width=4.5, ax=ax
        )

    # Draw failed edges
    if failed_edges:
        nx.draw_networkx_edges(
            manager.base_graph, pos, edgelist=failed_edges,
            edge_color="#dc3545", width=2.5, style="dashed", ax=ax
        )

    # Classify nodes
    active_nodes = []
    failed_nodes = []
    route_node_list = []

    for node in manager.base_graph.nodes():
        if not manager.is_node_active(node):
            failed_nodes.append(node)
        elif node in route_nodes:
            route_node_list.append(node)
        else:
            active_nodes.append(node)

    # Draw nodes
    if active_nodes:
        nx.draw_networkx_nodes(
            manager.base_graph, pos, nodelist=active_nodes,
            node_color="#28a745", node_size=750, edgecolors="#1e7e34", linewidths=2, ax=ax
        )
    if route_node_list:
        nx.draw_networkx_nodes(
            manager.base_graph, pos, nodelist=route_node_list,
            node_color="#007bff", node_size=850, edgecolors="#0056b3", linewidths=2.5, ax=ax
        )
    if failed_nodes:
        nx.draw_networkx_nodes(
            manager.base_graph, pos, nodelist=failed_nodes,
            node_color="#dc3545", node_size=750, edgecolors="#bd2130", linewidths=2, ax=ax
        )

    # Draw labels
    labels = {n: n for n in manager.base_graph.nodes()}
    nx.draw_networkx_labels(
        manager.base_graph, pos, labels=labels,
        font_size=11, font_color="#ffffff", font_weight="bold", ax=ax
    )

    # Edge weight labels
    edge_labels = {
        (u, v): f"{manager.base_graph[u][v].get('weight', 1)}"
        for u, v in manager.base_graph.edges()
    }
    nx.draw_networkx_edge_labels(
        manager.base_graph, pos, edge_labels=edge_labels,
        font_size=9, font_color="#343a40", ax=ax
    )

    ax.set_title("MeshGuard Network Topology", fontsize=14, fontweight="bold", pad=15)
    ax.axis("off")
    fig.tight_layout()
    return fig
