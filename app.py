"""
app.py - MeshGuard: Self-Healing Computer Network Simulator
Streamlit web dashboard demonstrating network routing, failure detection,
automatic self-healing (Dijkstra rerouting), packet simulation, and live metrics.
"""

import datetime
import logging
import os
import time
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import networkx as nx
import streamlit as st
import streamlit.components.v1 as components

from healing.self_healing import SelfHealingEngine
from monitoring.failure_detector import FailureDetector
from network.manager import NetworkManager
from network.topology import normalize_edge
from network.visualizer import generate_matplotlib_figure, generate_pyvis_html
from routing.dijkstra import find_shortest_path
from simulation.packet import PacketSimulator

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="MeshGuard – Self-Healing Computer Network Simulator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------------------------------------
# Python Logging Setup
# ---------------------------------------------------------
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meshguard.log")
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("MeshGuard")


# ---------------------------------------------------------
# Helper Functions for Logging & State
# ---------------------------------------------------------
def log_event(message: str) -> None:
    """Adds a timestamped entry to session logs and file logger."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"{timestamp} - {message}"
    if "event_logs" not in st.session_state:
        st.session_state.event_logs = []
    st.session_state.event_logs.append(entry)
    logger.info(message)


def init_session_state():
    """Initializes Streamlit session state objects if not already set."""
    if "manager" not in st.session_state:
        st.session_state.manager = NetworkManager()
    if "packet_sim" not in st.session_state:
        st.session_state.packet_sim = PacketSimulator()
    if "event_logs" not in st.session_state:
        st.session_state.event_logs = []
        log_event("MeshGuard started - Topology initialized with 8 routers")
    if "current_route" not in st.session_state:
        st.session_state.current_route = None
    if "current_cost" not in st.session_state:
        st.session_state.current_cost = None
    if "route_hops" not in st.session_state:
        st.session_state.route_hops = []
    if "last_healing_event" not in st.session_state:
        st.session_state.last_healing_event = None
    if "last_recovery_time" not in st.session_state:
        st.session_state.last_recovery_time = None
    if "packet_logs" not in st.session_state:
        st.session_state.packet_logs = []
    if "source_router" not in st.session_state:
        st.session_state.source_router = "A"
    if "dest_router" not in st.session_state:
        st.session_state.dest_router = "H"
    if "monitoring_banner" not in st.session_state:
        st.session_state.monitoring_banner = "MeshGuard monitoring network... All systems operational."


init_session_state()

manager: NetworkManager = st.session_state.manager
packet_sim: PacketSimulator = st.session_state.packet_sim

# ---------------------------------------------------------
# Custom Styling
# ---------------------------------------------------------
st.markdown("""
<style>
    /* Global styling */
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1e293b;
        margin-bottom: 0.2rem;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 1.1rem;
        font-weight: 500;
        color: #64748b;
        margin-bottom: 1.2rem;
    }
    .status-badge {
        display: inline-block;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.95rem;
        margin-bottom: 1rem;
        color: #ffffff;
    }
    .card-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .healing-alert {
        background-color: #fffbeb;
        border-left: 5px solid #f59e0b;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 16px;
        color: #92400e;
    }
    .recovered-alert {
        background-color: #ecfdf5;
        border-left: 5px solid #10b981;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 16px;
        color: #065f46;
    }
    .danger-alert {
        background-color: #fef2f2;
        border-left: 5px solid #ef4444;
        padding: 14px 18px;
        border-radius: 6px;
        margin-bottom: 16px;
        color: #991b1b;
    }
    .log-container {
        background-color: #0f172a;
        color: #38bdf8;
        font-family: 'Courier New', Courier, monospace;
        font-size: 0.85rem;
        border-radius: 8px;
        padding: 14px;
        height: 240px;
        overflow-y: scroll;
    }
    .route-display {
        font-family: 'Courier New', Courier, monospace;
        font-weight: 700;
        font-size: 1.15rem;
        color: #0284c7;
        background: #f0f9ff;
        padding: 8px 12px;
        border-radius: 6px;
        border: 1px dashed #38bdf8;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)


# ---------------------------------------------------------
# Evaluate Network Health
# ---------------------------------------------------------
health_info = FailureDetector.evaluate_network_health(
    manager,
    st.session_state.source_router,
    st.session_state.dest_router
)

# ---------------------------------------------------------
# Header & Network Status Banner
# ---------------------------------------------------------
st.markdown("<div class='main-title'>🛡️ MeshGuard – Self-Healing Computer Network Simulator</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Dynamic Fault-Tolerant Network Routing & Real-Time Self-Healing Protocol Simulator</div>", unsafe_allow_html=True)

# Top Status Indicators
status_col1, status_col2 = st.columns([2, 3])
with status_col1:
    if health_info["status"] == FailureDetector.HEALTH_HEALTHY:
        st.markdown("<div class='status-badge' style='background-color:#16a34a;'>🟢 HEALTHY</div>", unsafe_allow_html=True)
    elif health_info["status"] == FailureDetector.HEALTH_DEGRADED:
        st.markdown("<div class='status-badge' style='background-color:#d97706;'>🟡 RECOVERED / DEGRADED</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='status-badge' style='background-color:#dc2626;'>🔴 NETWORK DISCONNECTED</div>", unsafe_allow_html=True)

with status_col2:
    st.info(f"📡 **Monitor Status:** {st.session_state.monitoring_banner}", icon="ℹ️")

# ---------------------------------------------------------
# Dashboard Statistics
# ---------------------------------------------------------
net_stats = manager.get_statistics()
pkt_stats = packet_sim.get_stats()
rec_time_str = f"{st.session_state.last_recovery_time:.3f} s" if st.session_state.last_recovery_time is not None else "0.000 s"

m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7, m_col8, m_col9, m_col10 = st.columns(10)
m_col1.metric("Total Routers", net_stats["total_routers"])
m_col2.metric("Active Routers", net_stats["active_routers"])
m_col3.metric("Failed Routers", net_stats["failed_routers"])
m_col4.metric("Total Links", net_stats["total_links"])
m_col5.metric("Active Links", net_stats["active_links"])
m_col6.metric("Failed Links", net_stats["failed_links"])
m_col7.metric("Packets Sent", pkt_stats["packets_sent"])
m_col8.metric("Delivered", pkt_stats["packets_delivered"])
m_col9.metric("Lost", pkt_stats["packets_lost"])
m_col10.metric("Recovery Time", rec_time_str)

st.divider()

# ---------------------------------------------------------
# Self-Healing Alert Notification (If active)
# ---------------------------------------------------------
healing_event = st.session_state.last_healing_event
if healing_event:
    if healing_event["status"] == "RECOVERED":
        orig_str = " → ".join(healing_event["original_path"]) if healing_event["original_path"] else "None"
        new_str = " → ".join(healing_event["recovered_path"])
        st.markdown(f"""
        <div class='recovered-alert'>
            <strong>⚠ Failure Detected & Self-Healing Triggered</strong><br>
            • <strong>Failed Element:</strong> {healing_event['failure_type']} <code>{healing_event['failed_item']}</code><br>
            • <strong>Original Route:</strong> <span style='text-decoration:line-through; color:#6b7280;'>{orig_str}</span><br>
            • <strong>Recalculating route...</strong> Alternative shortest path computed via Dijkstra.<br>
            • <strong>Alternative Route:</strong> <strong>{new_str}</strong> (Cost: {healing_event['recovered_cost']})<br>
            • <strong>✓ Network Successfully Recovered</strong> | <strong>Recovery Time:</strong> {healing_event['recovery_time']:.3f} seconds
        </div>
        """, unsafe_allow_html=True)
    elif healing_event["status"] == "FAILED_NO_PATH":
        st.markdown(f"""
        <div class='danger-alert'>
            <strong>⚠ Network Failure Detected</strong><br>
            • <strong>Failed Element:</strong> {healing_event['failure_type']} <code>{healing_event['failed_item']}</code><br>
            • <strong>Status:</strong> Network could not recover because no alternative path is available between {st.session_state.source_router} and {st.session_state.dest_router}.<br>
            • <strong>Action Required:</strong> Restore routers or links to re-establish connectivity.
        </div>
        """, unsafe_allow_html=True)
    elif healing_event["status"] == "UNAFFECTED":
        st.markdown(f"""
        <div class='healing-alert'>
            <strong>ℹ Failure Detected</strong><br>
            • <strong>Failed Element:</strong> {healing_event['failure_type']} <code>{healing_event['failed_item']}</code><br>
            • <strong>Active Route Status:</strong> The current active route is not traversing this element. Routing remains operational.
        </div>
        """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Main Two-Column Layout
# ---------------------------------------------------------
left_col, right_col = st.columns([1.35, 1.0], gap="medium")

# =========================================================
# LEFT COLUMN: Network Visualization & Route Details
# =========================================================
with left_col:
    st.subheader("🌐 Network Topology Visualization")

    viz_mode = st.radio(
        "Visualization Engine",
        options=["Interactive Network (PyVis)", "Static Graph (Matplotlib)"],
        horizontal=True,
        label_visibility="collapsed"
    )

    # Topology Legend
    st.caption("🟢 **Active Router** | 🔴 **Failed Router** | 🔵 **Active Route** | ── **Active Link** | ┈┈ **Failed Link**")

    if viz_mode == "Interactive Network (PyVis)":
        html_content = generate_pyvis_html(manager, st.session_state.current_route, height="470px")
        components.html(html_content, height=480, scrolling=False)
    else:
        fig = generate_matplotlib_figure(manager, st.session_state.current_route)
        st.pyplot(fig)
        plt.close(fig)

    # Route info banner
    if st.session_state.current_route:
        route_arrow = " → ".join(st.session_state.current_route)
        st.markdown(f"""
        <div class='card-box' style='padding: 12px 16px;'>
            <strong>Current Active Route:</strong> <span class='route-display'>{route_arrow}</span><br>
            <span style='margin-top:6px; display:inline-block;'><strong>Total Cost:</strong> <code>{st.session_state.current_cost}</code> | <strong>Hops:</strong> <code>{len(st.session_state.current_route) - 1}</code></span>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("💡 Select a Source and Destination router on the right, then click **Find Best Route**.", icon="📌")

    # Packet hop transmission results
    if st.session_state.packet_logs:
        st.markdown("##### 📦 Latest Packet Transmission Log")
        packet_box = ""
        for plog in st.session_state.packet_logs:
            if "[OK]" in plog:
                packet_box += f"<span style='color:#10b981; font-weight:600;'>{plog}</span><br>"
            elif "[FAIL]" in plog or "dropped" in plog:
                packet_box += f"<span style='color:#ef4444; font-weight:600;'>{plog}</span><br>"
            else:
                packet_box += f"<span style='color:#0284c7;'>{plog}</span><br>"
        st.markdown(f"<div style='background:#f8fafc; border:1px solid #cbd5e1; border-radius:6px; padding:10px 14px; font-family:monospace; font-size:0.85rem;'>{packet_box}</div>", unsafe_allow_html=True)


# =========================================================
# RIGHT COLUMN: Routing, Simulation, Failures & Recovery
# =========================================================
with right_col:

    # -----------------------------------------------------
    # SECTION 1: Source & Destination Routing
    # -----------------------------------------------------
    st.subheader("📍 Routing & Path Calculation")
    all_routers = sorted(list(manager.base_graph.nodes))

    r_col1, r_col2 = st.columns(2)
    with r_col1:
        source_idx = all_routers.index(st.session_state.source_router) if st.session_state.source_router in all_routers else 0
        source_selection = st.selectbox("Source Router", options=all_routers, index=source_idx)
        st.session_state.source_router = source_selection

    with r_col2:
        dest_idx = all_routers.index(st.session_state.dest_router) if st.session_state.dest_router in all_routers else len(all_routers) - 1
        dest_selection = st.selectbox("Destination Router", options=all_routers, index=dest_idx)
        st.session_state.dest_router = dest_selection

    btn_col1, btn_col2 = st.columns(2)
    with btn_col1:
        find_route_btn = st.button("🔍 Find Best Route", use_container_width=True, type="primary")

    with btn_col2:
        send_packet_btn = st.button("🚀 Send Packet", use_container_width=True)

    # Action: Find Best Route
    if find_route_btn:
        if source_selection == dest_selection:
            st.warning("Source and Destination routers cannot be the same!")
        elif not manager.is_node_active(source_selection):
            st.error(f"Cannot calculate route: Source Router {source_selection} is currently FAILED!")
        elif not manager.is_node_active(dest_selection):
            st.error(f"Cannot calculate route: Destination Router {dest_selection} is currently FAILED!")
        else:
            active_g = manager.get_active_graph()
            path, cost, hops = find_shortest_path(active_g, source_selection, dest_selection)

            if path is not None:
                st.session_state.current_route = path
                st.session_state.current_cost = cost
                st.session_state.route_hops = hops
                st.session_state.last_healing_event = None
                route_str = " → ".join(path)
                log_event(f"Route calculated: {route_str} (Cost: {cost})")
                st.success(f"Best Route found: **{route_str}** | Total Cost: **{cost}**")
                st.rerun()
            else:
                st.session_state.current_route = None
                st.session_state.current_cost = None
                st.session_state.route_hops = []
                log_event(f"Route calculation failed: No available path between {source_selection} and {dest_selection}")
                st.error("No path exists between the selected routers on the active network!")
                st.rerun()

    # Action: Send Packet
    if send_packet_btn:
        if not st.session_state.current_route:
            st.warning("Please find a route first before sending packets.")
        else:
            trans_result = packet_sim.transmit_packet(st.session_state.current_route, manager)
            st.session_state.packet_logs = trans_result["hop_logs"]

            # Log hop events
            for hop_msg in trans_result["hop_logs"]:
                log_event(hop_msg)

            if trans_result["success"]:
                st.toast("Packet delivered successfully!", icon="✔")
            else:
                st.toast("Packet dropped during transmission!", icon="❌")
            st.rerun()

    st.divider()

    # -----------------------------------------------------
    # SECTION 2: Failure Simulation
    # -----------------------------------------------------
    st.subheader("⚡ Failure Simulation")

    tab_link_fail, tab_node_fail = st.tabs(["Link Failure", "Router Failure"])

    # --- Link Failure Tab ---
    with tab_link_fail:
        active_links = manager.get_active_links()
        link_options = [f"{u} - {v}" for u, v in active_links]

        if not link_options:
            st.info("All network links are currently failed.")
        else:
            selected_link_str = st.selectbox("Select Network Link to Fail", options=link_options)
            fail_link_btn = st.button("💥 Fail Link", use_container_width=True, type="secondary")

            if fail_link_btn and selected_link_str:
                u, v = selected_link_str.split(" - ")
                if manager.fail_link(u, v):
                    st.session_state.monitoring_banner = f"Failure detected: Link {u} <-> {v}"
                    log_event(f"Link {u}-{v} failed")
                    log_event(f"Failure detected: Link {u} <-> {v}")

                    # Trigger Self-Healing if route exists
                    if st.session_state.current_route:
                        log_event("MeshGuard monitoring network...")
                        log_event("Self-healing initiated")
                        healing_res = SelfHealingEngine.trigger_healing(
                            manager=manager,
                            source=st.session_state.source_router,
                            destination=st.session_state.dest_router,
                            current_path=st.session_state.current_route,
                            failure_type="Link",
                            failed_item=f"{u}-{v}"
                        )
                        st.session_state.last_healing_event = healing_res
                        st.session_state.last_recovery_time = healing_res["recovery_time"]

                        if healing_res["status"] == "RECOVERED":
                            st.session_state.current_route = healing_res["recovered_path"]
                            st.session_state.current_cost = healing_res["recovered_cost"]
                            st.session_state.route_hops = healing_res["hops_detail"]
                            new_r_str = " → ".join(healing_res["recovered_path"])
                            log_event(f"Alternative route found: {new_r_str}")
                            log_event(f"Network successfully recovered in {healing_res['recovery_time']:.3f}s")
                        elif healing_res["status"] == "FAILED_NO_PATH":
                            st.session_state.current_route = None
                            st.session_state.current_cost = None
                            st.session_state.route_hops = []
                            log_event("Network could not recover: No alternative path available")
                    st.rerun()

    # --- Router Failure Tab ---
    with tab_node_fail:
        active_routers = manager.get_active_nodes()

        if not active_routers:
            st.info("All routers are currently failed.")
        else:
            selected_router = st.selectbox("Select Router to Fail", options=active_routers)
            fail_router_btn = st.button("🛑 Fail Router", use_container_width=True, type="secondary")

            if fail_router_btn and selected_router:
                if manager.fail_node(selected_router):
                    st.session_state.monitoring_banner = f"Failure detected: Router {selected_router}"
                    log_event(f"Router {selected_router} failed")
                    log_event(f"Failure detected: Router {selected_router}")
                    log_event(f"All links connected to Router {selected_router} became unavailable")

                    # Trigger Self-Healing if route exists
                    if st.session_state.current_route:
                        log_event("MeshGuard monitoring network...")
                        log_event("Self-healing initiated")
                        healing_res = SelfHealingEngine.trigger_healing(
                            manager=manager,
                            source=st.session_state.source_router,
                            destination=st.session_state.dest_router,
                            current_path=st.session_state.current_route,
                            failure_type="Router",
                            failed_item=selected_router
                        )
                        st.session_state.last_healing_event = healing_res
                        st.session_state.last_recovery_time = healing_res["recovery_time"]

                        if healing_res["status"] == "RECOVERED":
                            st.session_state.current_route = healing_res["recovered_path"]
                            st.session_state.current_cost = healing_res["recovered_cost"]
                            st.session_state.route_hops = healing_res["hops_detail"]
                            new_r_str = " → ".join(healing_res["recovered_path"])
                            log_event(f"Alternative route found: {new_r_str}")
                            log_event(f"Network successfully recovered in {healing_res['recovery_time']:.3f}s")
                        elif healing_res["status"] == "FAILED_NO_PATH":
                            st.session_state.current_route = None
                            st.session_state.current_cost = None
                            st.session_state.route_hops = []
                            log_event("Network could not recover: No alternative path available")
                    st.rerun()

    st.divider()

    # -----------------------------------------------------
    # SECTION 3: Recovery Controls
    # -----------------------------------------------------
    st.subheader("🔧 Recovery & Restoration Controls")

    rec_tab_link, rec_tab_node = st.tabs(["Restore Link", "Restore Router"])

    with rec_tab_link:
        failed_links = manager.get_failed_links()
        if not failed_links:
            st.success("All links are operational. None failed.", icon="✔")
        else:
            failed_link_options = [f"{u} - {v}" for u, v in failed_links]
            selected_failed_link = st.selectbox("Select Failed Link to Restore", options=failed_link_options)
            restore_link_btn = st.button("🔄 Restore Link", use_container_width=True)

            if restore_link_btn and selected_failed_link:
                u, v = selected_failed_link.split(" - ")
                if manager.restore_link(u, v):
                    log_event(f"Link {u}-{v} successfully restored")
                    st.session_state.monitoring_banner = f"Link {u}-{v} successfully restored"

                    # Check if restoring optimizes or re-establishes route
                    if manager.is_node_active(st.session_state.source_router) and manager.is_node_active(st.session_state.dest_router):
                        active_g = manager.get_active_graph()
                        p, c, h = find_shortest_path(active_g, st.session_state.source_router, st.session_state.dest_router)
                        if p:
                            st.session_state.current_route = p
                            st.session_state.current_cost = c
                            st.session_state.route_hops = h
                            log_event(f"Optimal route updated after link restoration: {' → '.join(p)} (Cost: {c})")
                    st.rerun()

    with rec_tab_node:
        failed_routers = manager.get_failed_nodes()
        if not failed_routers:
            st.success("All routers are operational. None failed.", icon="✔")
        else:
            selected_failed_router = st.selectbox("Select Failed Router to Restore", options=failed_routers)
            restore_router_btn = st.button("🔄 Restore Router", use_container_width=True)

            if restore_router_btn and selected_failed_router:
                if manager.restore_node(selected_failed_router):
                    log_event(f"Router {selected_failed_router} successfully restored")
                    st.session_state.monitoring_banner = f"Router {selected_failed_router} successfully restored"

                    # Re-evaluate path
                    if manager.is_node_active(st.session_state.source_router) and manager.is_node_active(st.session_state.dest_router):
                        active_g = manager.get_active_graph()
                        p, c, h = find_shortest_path(active_g, st.session_state.source_router, st.session_state.dest_router)
                        if p:
                            st.session_state.current_route = p
                            st.session_state.current_cost = c
                            st.session_state.route_hops = h
                            log_event(f"Optimal route updated after router restoration: {' → '.join(p)} (Cost: {c})")
                    st.rerun()

    # Reset Network Button
    st.write("")
    reset_btn = st.button("♻ Reset Network to Default", use_container_width=True)
    if reset_btn:
        manager.reset_network()
        packet_sim.reset_metrics()
        st.session_state.current_route = None
        st.session_state.current_cost = None
        st.session_state.route_hops = []
        st.session_state.last_healing_event = None
        st.session_state.last_recovery_time = None
        st.session_state.packet_logs = []
        st.session_state.monitoring_banner = "Network reset to default state. All routers and links active."
        log_event("Network reset - All routers and links restored to ACTIVE")
        st.rerun()

st.divider()

# ---------------------------------------------------------
# SECTION 4: Network Event Logs & Hop Breakdown
# ---------------------------------------------------------
log_col1, log_col2 = st.columns([1.4, 1.0], gap="medium")

with log_col1:
    st.subheader("📜 Network Event Logs")
    visible_logs = st.session_state.event_logs[-30:]
    log_text = "\n".join(visible_logs)
    st.markdown(f"<div class='log-container'>{log_text.replace(chr(10), '<br>')}</div>", unsafe_allow_html=True)
    st.caption(f"Displaying latest {len(visible_logs)} events. Complete logs saved to `meshguard.log`.")

with log_col2:
    st.subheader("📊 Hop-by-Hop Route Breakdown")
    if st.session_state.route_hops:
        st.dataframe(
            st.session_state.route_hops,
            column_config={
                "hop": "Hop #",
                "from": "From Router",
                "to": "To Router",
                "link": "Link",
                "cost": "Hop Cost",
                "cumulative_cost": "Cumulative Cost"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No active route currently calculated. Use 'Find Best Route' to see hop details.")

