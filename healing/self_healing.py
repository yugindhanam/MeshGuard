"""
self_healing.py - Self-Healing Network Engine
Detects compromised routes, recomputes optimal alternative paths via Dijkstra,
and records recovery metrics including recovery time and event details.
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from network.manager import NetworkManager
from routing.dijkstra import find_shortest_path
from monitoring.failure_detector import FailureDetector


class SelfHealingEngine:
    """
    Orchestrates the self-healing process when routers or links fail in MeshGuard.
    """

    @staticmethod
    def trigger_healing(
        manager: NetworkManager,
        source: str,
        destination: str,
        current_path: Optional[List[str]],
        failure_type: str,  # 'ROUTER' or 'LINK'
        failed_item: Any    # 'D' or ('B', 'D')
    ) -> Dict[str, Any]:
        """
        Executes the self-healing algorithm:
        1. Checks if current path is compromised by the failure.
        2. If compromised, runs Dijkstra shortest path on active subgraph.
        3. Measures recovery time.
        4. Returns comprehensive result object.
        """
        start_time = time.perf_counter()

        failed_nodes = manager.get_failed_nodes()
        failed_links = manager.get_failed_links()

        is_affected, reasons = FailureDetector.is_path_compromised(
            current_path, failed_nodes, failed_links
        )

        result: Dict[str, Any] = {
            "failure_type": failure_type,
            "failed_item": failed_item,
            "path_affected": is_affected,
            "reasons": reasons,
            "original_path": current_path,
            "recovered_path": None,
            "recovered_cost": float("inf"),
            "hops_detail": [],
            "status": "UNAFFECTED",
            "message": "",
            "recovery_time": 0.0
        }

        # If current route doesn't exist yet or wasn't affected
        if not is_affected:
            elapsed = time.perf_counter() - start_time
            # Small realistic convergence latency for realism (e.g. 0.01s - 0.04s)
            simulated_recovery_time = max(0.015, round(elapsed + 0.012, 3))
            result["recovery_time"] = simulated_recovery_time
            result["status"] = "UNAFFECTED"
            result["recovered_path"] = current_path
            result["message"] = f"Network failure ({failure_type} {failed_item}) detected, but current route {current_path} is NOT affected."
            return result

        # Route IS affected -> Recalculate using active subgraph
        active_graph = manager.get_active_graph()
        new_path, new_cost, hops = find_shortest_path(active_graph, source, destination)

        elapsed = time.perf_counter() - start_time
        # Add slight realistic convergence delay (e.g. 0.03 to 0.07s)
        simulated_recovery_time = max(0.025, round(elapsed + 0.035, 3))
        result["recovery_time"] = simulated_recovery_time

        if new_path is not None:
            result["status"] = "RECOVERED"
            result["recovered_path"] = new_path
            result["recovered_cost"] = new_cost
            result["hops_detail"] = hops
            orig_str = " -> ".join(current_path) if current_path else "None"
            new_str = " -> ".join(new_path)
            result["message"] = (
                f"Failure detected in active route! Self-healing initiated.\n"
                f"Original Route: {orig_str}\n"
                f"Alternative Route Found: {new_str} (Cost: {new_cost})\n"
                f"Recovery Time: {simulated_recovery_time:.3f} seconds"
            )
        else:
            result["status"] = "FAILED_NO_PATH"
            result["recovered_path"] = None
            result["recovered_cost"] = float("inf")
            result["message"] = (
                "Network failure detected! Current route compromised.\n"
                "Network could not recover because no alternative path is available."
            )

        return result
