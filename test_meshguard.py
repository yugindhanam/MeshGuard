"""
test_meshguard.py - Verification script for core MeshGuard modules
"""

from network.manager import NetworkManager
from routing.dijkstra import find_shortest_path
from monitoring.failure_detector import FailureDetector
from healing.self_healing import SelfHealingEngine
from simulation.packet import PacketSimulator


def test_core():
    print("--- 1. Testing Topology & NetworkManager ---")
    manager = NetworkManager()
    stats = manager.get_statistics()
    print("Initial stats:", stats)
    assert stats["total_routers"] == 8
    assert stats["active_routers"] == 8
    assert stats["failed_routers"] == 0
    assert stats["total_links"] == 13

    print("\n--- 2. Testing Shortest Path Routing (A to H) ---")
    active_g = manager.get_active_graph()
    path, cost, hops = find_shortest_path(active_g, "A", "H")
    print(f"Path: {' -> '.join(path)}, Cost: {cost}")
    assert path == ["A", "B", "D", "F", "H"], f"Unexpected path: {path}"
    assert cost == 10.0, f"Expected cost 10, got {cost}"
    print("Hops detail:")
    for h in hops:
        print(f"  {h['link']} (cost {h['cost']}, cumulative {h['cumulative_cost']})")

    print("\n--- 3. Testing Packet Transmission ---")
    packet_sim = PacketSimulator()
    res = packet_sim.transmit_packet(path, manager)
    print("Packet transmission success:", res["success"])
    for l in res["hop_logs"]:
        print("  " + l)
    assert res["success"] is True
    assert packet_sim.packets_sent == 1
    assert packet_sim.packets_delivered == 1
    assert packet_sim.packets_lost == 0

    print("\n--- 4. Testing Link Failure & Self-Healing (Fail D-F) ---")
    assert manager.fail_link("D", "F") is True
    # Attempting to fail again should return False
    assert manager.fail_link("D", "F") is False

    healing_result = SelfHealingEngine.trigger_healing(
        manager=manager,
        source="A",
        destination="H",
        current_path=path,
        failure_type="LINK",
        failed_item=("D", "F")
    )
    print("Healing Status:", healing_result["status"])
    print("Path Affected:", healing_result["path_affected"])
    print("Reasons:", healing_result["reasons"])
    print("Recovered Path:", healing_result["recovered_path"])
    print("Recovered Cost:", healing_result["recovered_cost"])
    print(f"Recovery Time: {healing_result['recovery_time']:.4f}s")
    assert healing_result["status"] == "RECOVERED"
    assert healing_result["path_affected"] is True
    assert "D" not in healing_result["recovered_path"] or "F" not in healing_result["recovered_path"] or healing_result["recovered_path"] != path

    # Health check
    health = FailureDetector.evaluate_network_health(manager, "A", "H")
    print("Health after link failure:", health["status"])
    assert health["status"] == FailureDetector.HEALTH_DEGRADED

    # Test packet on recovered path
    new_path = healing_result["recovered_path"]
    res2 = packet_sim.transmit_packet(new_path, manager)
    assert res2["success"] is True

    print("\n--- 5. Testing Router Failure (Fail D) ---")
    assert manager.fail_node("D") is True
    healing_result_node = SelfHealingEngine.trigger_healing(
        manager=manager,
        source="A",
        destination="H",
        current_path=new_path,
        failure_type="ROUTER",
        failed_item="D"
    )
    print("Node Failure Healing Status:", healing_result_node["status"])
    print("Recovered Path:", healing_result_node["recovered_path"])
    print("Recovered Cost:", healing_result_node["recovered_cost"])
    if healing_result_node["recovered_path"]:
        assert "D" not in healing_result_node["recovered_path"]

    print("\n--- 6. Testing Network Disconnection (Isolate H) ---")
    manager.fail_node("F")
    manager.fail_node("G")
    health_disc = FailureDetector.evaluate_network_health(manager, "A", "H")
    print("Health after isolating H:", health_disc["status"])
    assert health_disc["status"] == FailureDetector.HEALTH_DISCONNECTED

    healing_disc = SelfHealingEngine.trigger_healing(
        manager=manager,
        source="A",
        destination="H",
        current_path=["A", "C", "E", "G", "H"],
        failure_type="ROUTER",
        failed_item="G"
    )
    print("Disconnected Status:", healing_disc["status"])
    assert healing_disc["status"] == "FAILED_NO_PATH"
    assert healing_disc["recovered_path"] is None

    print("\n--- 7. Testing Restoration & Reset ---")
    manager.restore_node("D")
    assert manager.is_node_active("D") is True
    manager.restore_link("D", "F")
    assert manager.is_link_active("D", "F") is True

    manager.reset_network()
    reset_stats = manager.get_statistics()
    print("Reset stats:", reset_stats)
    assert reset_stats["failed_routers"] == 0
    assert reset_stats["failed_links"] == 0
    health_reset = FailureDetector.evaluate_network_health(manager, "A", "H")
    assert health_reset["status"] == FailureDetector.HEALTH_HEALTHY

    print("\n>>> ALL CORE TESTS PASSED SUCCESSFULLY! <<<")


if __name__ == "__main__":
    test_core()
