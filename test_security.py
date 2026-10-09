"""Security enforcement and compatibility regression scenarios."""

import unittest
from unittest.mock import patch

import matplotlib.pyplot as plt
from network.manager import NetworkManager
from network.visualizer import generate_matplotlib_figure, generate_pyvis_html
from routing.dijkstra import find_shortest_path
from security.monitor import SecurityMonitor
from security.threat_detector import SecurityPolicy
from simulation.packet import PacketSimulator


class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.manager = NetworkManager()
        self.packets = PacketSimulator()
        self.monitor = SecurityMonitor(self.manager, self.packets)
        self.client = self.monitor.clients["Client 2"]

    def test_three_normal_clients_reach_database(self):
        for name, client in self.monitor.clients.items():
            self.assertEqual(client.status, "NORMAL")
            self.assertTrue(self.monitor.request_database(name)["success"])
            self.assertEqual(client.route[-1], "H")
        self.assertEqual(self.packets.packets_delivered, 3)

    def test_attack_blocked_before_forwarding_and_recovered(self):
        with patch.object(self.packets, "transmit_packet", wraps=self.packets.transmit_packet) as send:
            result = self.monitor.simulate_attack("Client 2")
        self.assertTrue(result["blocked"])
        self.assertTrue(result["success"])
        self.assertEqual(send.call_count, 1)
        self.assertEqual(send.call_args.args[0], ["A", "B", "D", "F", "H"])
        self.assertEqual(self.client.status, "RECOVERED")
        self.assertLess(self.client.trust_score, 100)
        self.assertEqual(self.client.last_incident["classification"], "MALICIOUS")
        messages = "\n".join(e["message"] for e in self.monitor.events)
        for state in ["SUSPICIOUS", "MALICIOUS", "blocked", "Dijkstra", "RECOVERED"]:
            self.assertIn(state, messages)

    def test_other_clients_and_topology_unchanged(self):
        original = list(self.manager.base_graph.edges(data=True))
        self.monitor.simulate_attack("Client 2")
        for name in ["Client 1", "Client 3"]:
            client = self.monitor.clients[name]
            self.assertEqual((client.status, client.trust_score, client.delivered), ("NORMAL", 100, 0))
        self.assertEqual(list(self.manager.base_graph.edges(data=True)), original)
        self.assertEqual(len(self.manager.base_graph), 8)

    def test_invalid_routes(self):
        for path in [[], ["A", "X", "H"], ["A", "H"], ["B", "D", "H"],
                     ["A", "B"], ["A", "B", "A", "C", "E", "G", "H"],
                     "ABDFH", ["A", {}, "H"]]:
            with self.subTest(path=path):
                result = self.monitor.detector.validate(self.manager, self.client, path)
                self.assertEqual(result.status, "MALICIOUS")

    def test_untrusted_nodes_excluded_from_recovery(self):
        self.manager.base_graph.nodes["D"]["trusted"] = False
        self.assertFalse(self.manager.get_active_graph().nodes["D"]["trusted"])
        self.monitor.simulate_attack("Client 2")
        self.assertNotIn("D", self.client.route)

    def test_per_client_authorization_enforced(self):
        self.client.allowed_nodes = {"A", "C", "E", "G", "H"}
        self.monitor.request_database("Client 2", ["A", "B", "D", "H"])
        self.assertEqual(self.client.route, ["A", "C", "E", "G", "H"])
        self.assertIn("B", self.monitor.clients["Client 1"].route)

    def test_unexpected_trusted_route_is_suspicious_and_repeated_changes_scored(self):
        path = ["A", "C", "E", "G", "H"]
        for _ in range(3):
            self.monitor.request_database("Client 2", path)
        self.assertEqual(self.client.route_changes, 3)
        self.assertEqual(self.client.last_incident["classification"], "SUSPICIOUS")
        self.assertEqual(self.client.trust_score, 30)
        self.assertIn("Repeated client route changes", self.client.last_incident["reasons"])

    def test_configurable_scoring(self):
        monitor = SecurityMonitor(self.manager, self.packets,
                                  SecurityPolicy(unexpected_route_penalty=5))
        monitor.request_database("Client 2", ["A", "C", "E", "G", "H"])
        self.assertEqual(monitor.clients["Client 2"].trust_score, 95)

    def test_physical_failure_heals_without_malicious_label(self):
        self.manager.fail_link("D", "F")
        self.monitor.refresh_routes()
        for client in self.monitor.clients.values():
            self.assertEqual(client.status, "RECOVERED")
            self.assertEqual(client.trust_score, 100)
            self.assertIsNone(client.last_incident)
            self.assertTrue(self.monitor.request_database(client.client_id)["success"])
        self.manager.fail_node("D")
        self.monitor.simulate_attack("Client 2")
        self.assertNotIn("D", self.client.route)

    def test_disconnection_blocks_then_restoration_recovers(self):
        self.manager.fail_node("H")
        result = self.monitor.simulate_attack("Client 2")
        self.assertFalse(result["success"])
        self.assertEqual(self.client.status, "ISOLATED")
        self.assertIsNone(self.client.route)
        self.assertEqual(self.packets.packets_sent, 0)
        self.assertFalse(self.monitor.request_database("Client 2")["success"])
        count = len(self.monitor.events)
        self.monitor.refresh_routes()
        self.assertEqual(count, len(self.monitor.events))
        self.manager.restore_node("H")
        self.monitor.refresh_routes()
        self.assertTrue(self.monitor.request_database("Client 2")["success"])

    def test_no_authorized_path_fails_closed(self):
        self.client.allowed_nodes = {"A", "H"}
        self.assertFalse(self.monitor.simulate_attack("Client 2")["success"])
        self.assertEqual(self.client.status, "ISOLATED")
        self.assertEqual(self.packets.packets_sent, 0)

    def test_unknown_client_is_rejected(self):
        with self.assertRaises(ValueError):
            self.monitor.simulate_attack("Client 99")

    def test_mutated_client_route_is_detected_on_request(self):
        self.client.route = ["A", {}, "H"]
        self.assertTrue(self.monitor.request_database("Client 2")["success"])
        self.assertEqual(self.client.last_incident["classification"], "MALICIOUS")
        self.assertEqual(self.client.blocked_requests, 1)

    def test_missing_same_source_destination_is_not_reachable(self):
        self.assertIsNone(find_shortest_path(self.manager.get_active_graph(), "X", "X")[0])

    def test_visualization_overlay_does_not_change_network(self):
        self.monitor.simulate_attack("Client 2")
        kwargs = {"clients": list(self.monitor.clients.values()),
                  "blocked_path": self.client.last_incident["invalid_path"]}
        html = generate_pyvis_html(self.manager, self.client.route, **kwargs)
        for label in ["Client 1", "Client 2", "Client 3", "Database (H)", "BLOCKED", "Unauthorized X"]:
            self.assertIn(label, html)
        fig = generate_matplotlib_figure(self.manager, self.client.route, **kwargs)
        plt.close(fig)
        self.assertEqual(len(self.manager.base_graph), 8)
        self.assertEqual(len(self.manager.node_status), 8)
        self.assertEqual(len(self.manager.link_status), 13)


if __name__ == "__main__":
    unittest.main()
