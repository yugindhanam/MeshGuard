"""
visualizer.py - Enhanced Network Topology Visualizer (Cyber NOC Edition)
Generates high-tech interactive PyVis HTML networks and sleek dark-mode
Matplotlib graphs with glowing status indicators, route highlights, and metric labels.
"""

from typing import List, Optional, Tuple, Set
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
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
    height: str = "500px"
) -> str:
    """
    Constructs an interactive PyVis network graph with a Cyber NOC dark aesthetic:
    - Active router: Neon Emerald (#10b981)
    - Failed router: Crimson Red (#f43f5e)
    - Route router: Electric Cyan (#00e5ff)
    - Active link: Deep Slate Blue (#475569)
    - Route link: Glowing Electric Cyan (#00e5ff, width=6)
    - Failed link: Dashed Crimson Laser (#f43f5e, dashes=True)
    """
    net = Network(
        height=height,
        width="100%",
        bgcolor="#0b0f19",
        font_color="#f8fafc",
        notebook=False
    )
    net.toggle_physics(False)

    route_nodes = set(current_path or [])
    route_edges = get_route_edges(current_path)

    # Add Nodes with high-tech cyber styling
    for node in manager.base_graph.nodes:
        is_active = manager.is_node_active(node)
        is_on_route = node in route_nodes and is_active

        # Node coordinates from topology
        x_pos = manager.base_graph.nodes[node].get("x", 0) * 1.05
        y_pos = -manager.base_graph.nodes[node].get("y", 0) * 1.1

        if not is_active:
            bg_color = "#f43f5e"      # Neon Crimson
            border_color = "#e11d48"
            shadow_color = "rgba(244, 63, 94, 0.6)"
            title = f"<div style='font-family:monospace;padding:4px;'><strong>Router {node}</strong><br><span style='color:#f43f5e;'>STATUS: OFFLINE / FAILED</span></div>"
            label = f"Router {node}\n[OFFLINE]"
        elif is_on_route:
            bg_color = "#00e5ff"      # Electric Cyan
            border_color = "#38bdf8"
            shadow_color = "rgba(0, 229, 255, 0.7)"
            title = f"<div style='font-family:monospace;padding:4px;'><strong>Router {node}</strong><br><span style='color:#00e5ff;'>STATUS: ON ACTIVE ROUTE</span></div>"
            label = f"Router {node}\n[ROUTE]"
        else:
            bg_color = "#10b981"      # Neon Emerald
            border_color = "#34d399"
            shadow_color = "rgba(16, 185, 129, 0.5)"
            title = f"<div style='font-family:monospace;padding:4px;'><strong>Router {node}</strong><br><span style='color:#10b981;'>STATUS: OPERATIONAL</span></div>"
            label = f"Router {node}\n[ONLINE]"

        net.add_node(
            node,
            label=label,
            title=title,
            color={
                "background": bg_color,
                "border": border_color,
                "highlight": {"background": "#ffffff", "border": bg_color}
            },
            borderWidth=3,
            size=28,
            shape="dot",
            shadow={
                "enabled": True,
                "color": shadow_color,
                "size": 15,
                "x": 0,
                "y": 0
            },
            font={
                "color": "#ffffff",
                "size": 13,
                "face": "Inter, Segoe UI, sans-serif",
                "bold": True,
                "strokeWidth": 3,
                "strokeColor": "#0b0f19"
            },
            x=x_pos,
            y=y_pos,
            physics=False
        )

    # Add Edges with dynamic glow and dash effects
    for u, v, data in manager.base_graph.edges(data=True):
        edge_key = normalize_edge(u, v)
        weight = data.get("weight", 1)
        link_active = manager.is_link_active(u, v)
        both_nodes_active = manager.is_node_active(u) and manager.is_node_active(v)

        is_failed = (not link_active) or (not both_nodes_active)
        is_on_route = (edge_key in route_edges) and not is_failed

        edge_label = f" cost: {weight} "

        if is_failed:
            edge_color = "#f43f5e"
            width = 3
            dashes = [8, 8]
            status_desc = "LINK SEVERED" if not link_active else "DISABLED (Node Down)"
            title = f"<div style='font-family:monospace;padding:4px;'><strong>Link {u} <-> {v}</strong><br><span style='color:#f43f5e;'>{status_desc}</span><br>Cost: {weight}</div>"
        elif is_on_route:
            edge_color = "#00e5ff"
            width = 6
            dashes = False
            title = f"<div style='font-family:monospace;padding:4px;'><strong>Active Route Link {u} <-> {v}</strong><br><span style='color:#00e5ff;'>TRAFFIC FLOWING</span><br>Cost: {weight}</div>"
        else:
            edge_color = "#334155"
            width = 2.5
            dashes = False
            title = f"<div style='font-family:monospace;padding:4px;'><strong>Link {u} <-> {v}</strong><br>Operational<br>Cost: {weight}</div>"

        net.add_edge(
            u,
            v,
            label=edge_label,
            title=title,
            color=edge_color,
            width=width,
            dashes=dashes,
            font={
                "color": "#94a3b8" if not is_on_route else "#00e5ff",
                "size": 11,
                "face": "monospace",
                "background": "#0f172a",
                "strokeWidth": 0
            },
            smooth={"type": "continuous"}
        )

    # Enhanced options for dark cyber styling
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
    Renders a matching high-tech dark theme Matplotlib figure.
    """
    fig, ax = plt.subplots(figsize=(10, 6), dpi=120)
    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0b0f19")

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

    # 1. Base Active Edges
    if active_edges:
        nx.draw_networkx_edges(
            manager.base_graph, pos, edgelist=active_edges,
            edge_color="#334155", width=2.0, ax=ax
        )

    # 2. Highlighted Active Route Edges (with glowing width)
    if highlight_edges:
        nx.draw_networkx_edges(
            manager.base_graph, pos, edgelist=highlight_edges,
            edge_color="#00e5ff", width=5.0, ax=ax
        )

    # 3. Failed Edges (Crimson Dashed)
    if failed_edges:
        nx.draw_networkx_edges(
            manager.base_graph, pos, edgelist=failed_edges,
            edge_color="#f43f5e", width=2.5, style="dashed", ax=ax
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

    # Draw Nodes
    if active_nodes:
        nx.draw_networkx_nodes(
            manager.base_graph, pos, nodelist=active_nodes,
            node_color="#10b981", node_size=850, edgecolors="#34d399", linewidths=2.5, ax=ax
        )
    if route_node_list:
        nx.draw_networkx_nodes(
            manager.base_graph, pos, nodelist=route_node_list,
            node_color="#00e5ff", node_size=950, edgecolors="#ffffff", linewidths=3.0, ax=ax
        )
    if failed_nodes:
        nx.draw_networkx_nodes(
            manager.base_graph, pos, nodelist=failed_nodes,
            node_color="#f43f5e", node_size=850, edgecolors="#fda4af", linewidths=2.5, ax=ax
        )

    # Router Node Labels
    labels = {n: n for n in manager.base_graph.nodes()}
    nx.draw_networkx_labels(
        manager.base_graph, pos, labels=labels,
        font_size=11, font_color="#ffffff", font_weight="bold",
        font_family="monospace", ax=ax
    )

    # Edge Weight Labels
    edge_labels = {
        (u, v): f"{manager.base_graph[u][v].get('weight', 1)}"
        for u, v in manager.base_graph.edges()
    }
    nx.draw_networkx_edge_labels(
        manager.base_graph, pos, edge_labels=edge_labels,
        font_size=9, font_color="#cbd5e1", font_family="monospace",
        bbox=dict(boxstyle="round,pad=0.3", fc="#0f172a", ec="#334155", lw=1),
        ax=ax
    )

    ax.set_title("MeshGuard Topology – Live Telemetry Map", fontsize=13, fontweight="bold", color="#f8fafc", pad=14)
    ax.axis("off")
    fig.tight_layout()
    return fig
