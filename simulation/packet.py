"""
packet.py - Simulated Packet Transmission Engine
Simulates hop-by-hop packet forwarding along computed paths and tracks packet statistics.
"""

from typing import List, Dict, Tuple, Optional, Any
from network.manager import NetworkManager


class PacketSimulator:
    """
    Simulates packet flow across the network topology and maintains
    transmission metrics: sent, delivered, and lost.
    """

    def __init__(self):
        self.packets_sent: int = 0
        self.packets_delivered: int = 0
        self.packets_lost: int = 0

    def reset_metrics(self) -> None:
        """Resets all packet transmission counters."""
        self.packets_sent = 0
        self.packets_delivered = 0
        self.packets_lost = 0

    def transmit_packet(
        self,
        path: Optional[List[str]],
        manager: NetworkManager
    ) -> Dict[str, Any]:
        """
        Simulates forwarding a packet along the designated path.
        Verifies node and link health at each forwarding step.
        """
        self.packets_sent += 1
        hop_logs: List[str] = []

        if not path or len(path) < 2:
            self.packets_lost += 1
            return {
                "success": False,
                "hop_logs": ["Packet dropped: No valid route configured."],
                "reason": "No valid route exists between source and destination."
            }

        source = path[0]
        destination = path[-1]

        # 1. Packet creation
        hop_logs.append(f"Packet created at Router {source}")

        # Check source node status
        if not manager.is_node_active(source):
            self.packets_lost += 1
            hop_logs.append(f"❌ Transmission failed: Source Router {source} is DOWN.")
            return {
                "success": False,
                "hop_logs": hop_logs,
                "reason": f"Source Router {source} is down."
            }

        # 2. Hop-by-hop traversal
        for i in range(len(path) - 1):
            curr_node = path[i]
            next_node = path[i + 1]

            # Check if link is active
            if not manager.is_link_active(curr_node, next_node):
                self.packets_lost += 1
                hop_logs.append(f"[FAIL] Link Failure: Cannot forward from {curr_node} to {next_node}. Link is DOWN.")
                hop_logs.append("Packet dropped due to link failure.")
                return {
                    "success": False,
                    "hop_logs": hop_logs,
                    "reason": f"Link {curr_node} <-> {next_node} is failed."
                }

            # Check if next router is active
            if not manager.is_node_active(next_node):
                self.packets_lost += 1
                hop_logs.append(f"[FAIL] Node Failure: Router {next_node} unreachable (Router is DOWN).")
                hop_logs.append("Packet dropped due to router failure.")
                return {
                    "success": False,
                    "hop_logs": hop_logs,
                    "reason": f"Router {next_node} is failed."
                }

            hop_logs.append(f"Packet forwarded: Router {curr_node} -> Router {next_node}")

        # 3. Successful delivery
        self.packets_delivered += 1
        hop_logs.append(f"[OK] Packet successfully delivered to Destination Router {destination}.")

        return {
            "success": True,
            "hop_logs": hop_logs,
            "reason": None
        }

    def get_stats(self) -> Dict[str, int]:
        return {
            "packets_sent": self.packets_sent,
            "packets_delivered": self.packets_delivered,
            "packets_lost": self.packets_lost,
        }
