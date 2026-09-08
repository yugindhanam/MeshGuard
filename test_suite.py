"""
test_suite.py - Comprehensive End-to-End Verification Test Suite
Tests all 10 requirements and demo scenarios specified for MeshGuard.
"""

import unittest
import networkx as nx
from network.topology import load_topology_data, create_base_graph, normalize_edge
from network.manager import NetworkManager
from routing.dijkstra import find_shortest_path, dijkstra_trace
from monitoring.failure_detector import FailureDetector
from healing.self_healing import SelfHealingEngine
from simulation.packet import PacketSimulator
from network.visualizer import generate_pyvis_html, generate_matplotlib_figure


class TestMeshGuard(unittest.TestCase):

    def setUp(self):
        self.manager = NetworkManager()
        self.packet_sim = PacketSimulator()

    def test_01_topology_integrity(self):
        """Test initial network topology has 8 routers and redundant connections."""
        stats = self.manager.get_statistics()
        self.assertEqual(stats["total_routers"], 8)
        self.assertEqual(stats["active_routers"], 8)
        self.assertEqual(stats["failed_routers"], 0)
        self.assertGreaterEqual(stats["total_links"], 12)
        self.assertEqual(stats["active_links"], stats["total_links"])

        # Check all routers exist
        expected_routers = {"A", "B", "C", "D", "E", "F", "G", "H"}
        self.assertEqual(set(self.manager.base_graph.nodes), expected_routers)

    def test_02_dijkstra_normal_route(self):
        """Test finding best route between A and H."""
        active_g = self.manager.get_active_graph()
        path, cost, hops = find_shortest_path(active_g, "A", "H")
        self.assertEqual(path, ["A", "B", "D", "F", "H"])
        self.assertEqual(cost, 10.0)
        self.assertEqual(len(hops), 4)

    def test_03_packet_simulation_success(self):
        """Test simulated packet transmission along healthy route."""
        active_g = self.manager.get_active_graph()
        path, cost, hops = find_shortest_path(active_g, "A", "H")
        result = self.packet_sim.transmit_packet(path, self.manager)

        self.assertTrue(result["success"])
        self.assertEqual(self.packet_sim.packets_sent, 1)
        self.assertEqual(self.packet_sim.packets_delivered, 1)
        self.assertEqual(self.packet_sim.packets_lost, 0)
        self.assertIn("Packet created at Router A", result["hop_logs"][0])
        self.assertIn("Packet successfully delivered", result["hop_logs"][-1])

    def test_04_link_failure_and_self_healing(self):
        """Test link failure detection, automatic self-healing reroute, and recovery timing."""
        initial_path = ["A", "B", "D", "F", "H"]

        # Fail link D-F
        fail_ok = self.manager.fail_link("D", "F")
        self.assertTrue(fail_ok)
        self.assertFalse(self.manager.is_link_active("D", "F"))

        # Healing
        healing_result = SelfHealingEngine.trigger_healing(
            manager=self.manager,
            source="A",
            destination="H",
            current_path=initial_path,
            failure_type="Link",
            failed_item="D-F"
        )

        self.assertEqual(healing_result["status"], "RECOVERED")
        self.assertTrue(healing_result["path_affected"])
        self.assertGreater(healing_result["recovery_time"], 0.0)

        # Alternative route should not traverse failed link (D, F)
        rec_path = healing_result["recovered_path"]
        self.assertIsNotNone(rec_path)
        for i in range(len(rec_path) - 1):
            edge = normalize_edge(rec_path[i], rec_path[i + 1])
            self.assertNotEqual(edge, ("D", "F"))

        # Health should now be DEGRADED / RECOVERED
        health = FailureDetector.evaluate_network_health(self.manager, "A", "H")
        self.assertEqual(health["status"], FailureDetector.HEALTH_DEGRADED)

    def test_05_router_failure_and_cascade(self):
        """Test router failure disables router and all its incident links."""
        fail_ok = self.manager.fail_node("D")
        self.assertTrue(fail_ok)
        self.assertFalse(self.manager.is_node_active("D"))

        active_g = self.manager.get_active_graph()
        self.assertNotIn("D", active_g.nodes)

        # Healing reroute from A to H without router D
        healing = SelfHealingEngine.trigger_healing(
            manager=self.manager,
            source="A",
            destination="H",
            current_path=["A", "B", "D", "F", "H"],
            failure_type="Router",
            failed_item="D"
        )
        self.assertEqual(healing["status"], "RECOVERED")
        self.assertNotIn("D", healing["recovered_path"])

    def test_06_packet_loss_on_unhealed_failure(self):
        """Test that packets are dropped if attempted over a failed link without rerouting."""
        path = ["A", "B", "D", "F", "H"]
        self.manager.fail_link("B", "D")

        res = self.packet_sim.transmit_packet(path, self.manager)
        self.assertFalse(res["success"])
        self.assertEqual(self.packet_sim.packets_lost, 1)

    def test_07_disconnection_handling(self):
        """Test network disconnected detection when all alternative paths are severed."""
        # Isolate H completely
        self.manager.fail_node("F")
        self.manager.fail_node("G")
        self.manager.fail_link("D", "H")

        health = FailureDetector.evaluate_network_health(self.manager, "A", "H")
        self.assertEqual(health["status"], FailureDetector.HEALTH_DISCONNECTED)

        healing = SelfHealingEngine.trigger_healing(
            manager=self.manager,
            source="A",
            destination="H",
            current_path=["A", "B", "D", "F", "H"],
            failure_type="Node",
            failed_item="F"
        )
        self.assertEqual(healing["status"], "FAILED_NO_PATH")
        self.assertIsNone(healing["recovered_path"])

    def test_08_restoration(self):
        """Test restoring links and routers returns them to service."""
        self.manager.fail_node("C")
        self.manager.fail_link("A", "B")
        self.assertIn("C", self.manager.get_failed_nodes())
        self.assertIn(("A", "B"), self.manager.get_failed_links())

        # Restore
        self.assertTrue(self.manager.restore_node("C"))
        self.assertTrue(self.manager.restore_link("A", "B"))
        self.assertNotIn("C", self.manager.get_failed_nodes())
        self.assertNotIn(("A", "B"), self.manager.get_failed_links())

    def test_09_reset_network(self):
        """Test full network reset restores all nodes, links, and clears failures."""
        self.manager.fail_node("A")
        self.manager.fail_link("B", "D")
        self.packet_sim.transmit_packet(None, self.manager)

        self.manager.reset_network()
        self.packet_sim.reset_metrics()

        stats = self.manager.get_statistics()
        self.assertEqual(stats["failed_routers"], 0)
        self.assertEqual(stats["failed_links"], 0)
        self.assertEqual(self.packet_sim.packets_sent, 0)

    def test_10_visualizations(self):
        """Test that PyVis HTML and Matplotlib figure generators work cleanly."""
        path = ["A", "B", "D", "F", "H"]
        html = generate_pyvis_html(self.manager, path)
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 500)

        fig = generate_matplotlib_figure(self.manager, path)
        self.assertIsNotNone(fig)


if __name__ == "__main__":
    unittest.main(verbosity=2)

