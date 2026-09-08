"""
dijkstra.py - Shortest Path Calculation
Implements and wraps Dijkstra's shortest path algorithm for dynamic network routing.
"""

from typing import Tuple, List, Optional, Dict, Any
import heapq
import networkx as nx


def find_shortest_path(
    graph: nx.Graph,
    source: str,
    destination: str,
    weight: str = "weight"
) -> Tuple[Optional[List[str]], float, List[Dict[str, Any]]]:
    """
    Finds the shortest path and cost between source and destination using Dijkstra's algorithm.

    Returns:
        path: List of node IDs in sequence, or None if no route exists.
        cost: Total path cost (float('inf') if no route exists).
        hops_detail: List of hop descriptions with individual and cumulative costs.
    """
    if source == destination:
        return [source], 0.0, []

    if source not in graph or destination not in graph:
        return None, float("inf"), []

    try:
        # Use NetworkX Dijkstra implementation
        path = nx.dijkstra_path(graph, source, destination, weight=weight)
        cost = nx.dijkstra_path_length(graph, source, destination, weight=weight)

        # Build detailed hop-by-hop analysis for educational clarity
        hops_detail = []
        cumulative_cost = 0.0
        for i in range(len(path) - 1):
            u, v = path[i], path[i + 1]
            edge_cost = graph[u][v].get(weight, 1.0)
            cumulative_cost += edge_cost
            hops_detail.append({
                "hop": i + 1,
                "from": u,
                "to": v,
                "link": f"{u} -> {v}",
                "cost": edge_cost,
                "cumulative_cost": cumulative_cost
            })

        return path, cost, hops_detail

    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None, float("inf"), []


def dijkstra_trace(graph: nx.Graph, source: str) -> Dict[str, Any]:
    """
    Educational trace: Computes shortest distances from source to all reachable
    routers using min-heap Dijkstra, recording visited nodes and parent pointers.
    """
    if source not in graph:
        return {"distances": {}, "predecessors": {}}

    distances: Dict[str, float] = {node: float("inf") for node in graph.nodes}
    distances[source] = 0.0
    predecessors: Dict[str, Optional[str]] = {node: None for node in graph.nodes}

    pq: List[Tuple[float, str]] = [(0.0, source)]
    visited = set()

    while pq:
        curr_dist, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        for v in graph.neighbors(u):
            weight = graph[u][v].get("weight", 1.0)
            new_dist = curr_dist + weight
            if new_dist < distances[v]:
                distances[v] = new_dist
                predecessors[v] = u
                heapq.heappush(pq, (new_dist, v))

    return {
        "distances": distances,
        "predecessors": predecessors
    }
