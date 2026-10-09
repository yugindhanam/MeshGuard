"""
app.py - MeshGuard: Secure Self-Healing Computer Network Simulator
Advanced NOC Edition - High-Tech Network Telemetry, Self-Healing, and Route Security
"""

import datetime
import logging
import os
import re
import time
from typing import List, Optional, Tuple, Dict, Any

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
from security.monitor import SecurityMonitor
from security.panel import render_security_monitor
from ui.components import (
    load_styles,
    metric_card,
    section_heading,
    workflow_stepper,
    viva_demo_guide,
)

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="MeshGuard – Secure Self-Healing Network Simulator",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------------------------------------
# Python Logging Setup
# ---------------------------------------------------------
LOG_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "meshguard.log")
logging.basicConfig(
    filename=LOG_FILE_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("MeshGuard")


# ---------------------------------------------------------
# Helper Functions for Logging & State
# ---------------------------------------------------------
def log_event(message: str) -> None:
    """Adds a timestamped entry to session logs and file logger."""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    entry = f"[{timestamp}] {message}"
    if "event_logs" not in st.session_state:
        st.session_state.event_logs = []
    st.session_state.event_logs.append(entry)
    logger.info(message)


def parse_log_entry(raw_entry: str) -> Dict[str, str]:
    """Parses a raw log line into structured fields for audit table display."""
    time_match = re.search(r"\[(\d{2}:\d{2}:\d{2})\]", raw_entry)
    timestamp = time_match.group(1) if time_match else datetime.datetime.now().strftime("%H:%M:%S")
    body = raw_entry.replace(f"[{timestamp}]", "").strip()

    # Determine Severity
    if "[SECURITY]" in body and any(k in body for k in ["MALICIOUS", "SUSPICIOUS", "blocked", "penalty", "Blocked"]):
        severity = "SECURITY ALERT"
    elif any(k in body for k in ["[FAIL]", "dropped", "down", "Partitioned", "partition", "critical", "Down"]):
        severity = "ERROR"
    elif any(k in body for k in ["[MONITOR]", "degraded", "compromised", "offline"]):
        severity = "WARNING"
    else:
        severity = "INFO"

    # Determine Affected Entity
    if "Client 1" in body:
        affected = "Client 1"
    elif "Client 2" in body:
        affected = "Client 2"
    elif "Client 3" in body:
        affected = "Client 3"
    elif "Link " in body:
        link_m = re.search(r"Link\s+([A-Za-z0-9_\-\s<>]+)", body)
        affected = f"Link {link_m.group(1).strip()}" if link_m else "Network Link"
    elif "Router " in body:
        router_m = re.search(r"Router\s+([A-Za-z0-9_]+)", body)
        affected = f"Router {router_m.group(1)}" if router_m else "Router Node"
    else:
        affected = "Mesh Network"

    # Determine Action Taken
    if "[HEAL]" in body or "recalculation" in body.lower():
        action = "Autonomous Dijkstra Reroute"
    elif "[ROUTE]" in body:
        action = "Shortest Path Computation"
    elif "[PACKET]" in body:
        action = "Packet Forwarding"
    elif "[FAIL]" in body:
        action = "Element Failure Injected"
    elif "[RESTORE]" in body:
        action = "Element Restored to Service"
    elif "[RESET]" in body:
        action = "Full Topology Reset"
    elif "blocked" in body.lower():
        action = "Rogue Proposal Blocked"
    elif "safe route found" in body.lower():
        action = "Safe Route Re-established"
    else:
        action = "Telemetry Audit Log"

    clean_body = re.sub(r"\[(SYS|ROUTE|PACKET|FAIL|HEAL|MONITOR|SECURITY|RESTORE|RESET)\]", "", body).strip()

    return {
        "timestamp": timestamp,
        "severity": severity,
        "affected": affected,
        "event": clean_body,
        "action": action,
        "raw": raw_entry,
    }


def init_session_state() -> None:
    """Initializes Streamlit session state objects if not already set."""
    if "manager" not in st.session_state:
        st.session_state.manager = NetworkManager()
    if "packet_sim" not in st.session_state:
        st.session_state.packet_sim = PacketSimulator()
    if "event_logs" not in st.session_state:
        st.session_state.event_logs = []
        log_event("[SYS] MeshGuard Core Initialized - 8-Router Mesh Topology Active")
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

if "security_monitor" not in st.session_state:
    st.session_state.security_monitor = SecurityMonitor(manager, packet_sim, event_sink=log_event)

security_monitor: SecurityMonitor = st.session_state.security_monitor
security_monitor.event_sink = log_event
security_monitor.refresh_routes()

# ---------------------------------------------------------
# Cyber NOC Design System CSS
# ---------------------------------------------------------
load_styles()

# ---------------------------------------------------------
# Evaluate Network Health
# ---------------------------------------------------------
health_info = FailureDetector.evaluate_network_health(
    manager,
    st.session_state.source_router,
    st.session_state.dest_router,
)

status_class = "pill-healthy"
if health_info["status"] == FailureDetector.HEALTH_DEGRADED:
    status_class = "pill-degraded"
elif health_info["status"] == FailureDetector.HEALTH_DISCONNECTED:
    status_class = "pill-disconnected"

status_label = {
    "pill-healthy": "NETWORK HEALTHY",
    "pill-degraded": "NETWORK DEGRADED",
    "pill-disconnected": "NETWORK DISCONNECTED",
}[status_class]

# ---------------------------------------------------------
# Section 3.A: Dashboard Header
# ---------------------------------------------------------
st.markdown(f"""
<header class="app-masthead">
    <div class="brand">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true">
            <path d="M12 3 21 6v6c0 5-9 9-9 9S3 17 3 12V6l9-3Z"/>
            <path d="m7 12 3 3 7-7"/>
        </svg>
        <div>
            MeshGuard
            <small>Secure Self-Healing Network Simulator</small>
        </div>
    </div>
    <nav class="app-nav" aria-label="Workspace sections">
        <a href="#topology-workspace" target="_self">Topology & Telemetry</a>
        <a href="#failure-workspace" target="_self">Failure Testing</a>
        <a href="#security-workspace" target="_self">Security Testing</a>
        <a href="#logs-workspace" target="_self">Event Logs</a>
    </nav>
</header>
<section class="workspace-hero">
    <div>
        <div class="eyebrow">CONTROL CENTER / NETWORK OPERATIONS CENTER</div>
        <h1>MeshGuard</h1>
        <p style="color:#38bdf8; font-weight:600; margin-bottom:4px; font-size:15px;">Secure Self-Healing Network Simulator</p>
        <p>Monitor network health, detect failures, identify unauthorized routes, and automatically recover network connectivity.</p>
    </div>
    <div class="hero-meta">
        <span class="status-pill {status_class}"><span class="pulse-dot"></span>{status_label}</span>
        <small>8-Router Mesh &nbsp; · &nbsp; Dijkstra Dynamic Routing &nbsp; · &nbsp; Request Gate</small>
    </div>
</section>
""", unsafe_allow_html=True)

# Expandable Viva & Demo Walkthrough Guide (Section 10)
viva_demo_guide()

# ---------------------------------------------------------
# Section 3.B: Network Summary Cards
# ---------------------------------------------------------
net_stats = manager.get_statistics()
pkt_stats = packet_sim.get_stats()
rec_time_str = (
    f"{st.session_state.last_recovery_time:.3f} s"
    if st.session_state.last_recovery_time is not None
    else "No recovery yet"
)

# Real Simulation Metrics
total_clients = len(security_monitor.clients)
active_routers_val = f"{net_stats['active_routers']} / {net_stats['total_routers']}"
net_health_val = (
    "HEALTHY" if health_info["status"] == FailureDetector.HEALTH_HEALTHY
    else "DEGRADED" if health_info["status"] == FailureDetector.HEALTH_DEGRADED
    else "DISCONNECTED"
)
health_tone = "green" if net_health_val == "HEALTHY" else "amber" if net_health_val == "DEGRADED" else "red"

# Count active alerts (failed nodes + failed links + client security flags)
suspicious_or_malicious_clients = sum(
    1 for c in security_monitor.clients.values() if c.status in ("MALICIOUS", "SUSPICIOUS")
)
active_alerts_count = net_stats["failed_routers"] + net_stats["failed_links"] + suspicious_or_malicious_clients

# Dynamic Current Network Status text
has_malicious = any(c.status == "MALICIOUS" for c in security_monitor.clients.values())
if has_malicious:
    current_status_text = "Rogue Route Blocked"
    status_tone = "red"
elif health_info["status"] == FailureDetector.HEALTH_DISCONNECTED:
    current_status_text = "Network Partitioned"
    status_tone = "red"
elif health_info["status"] == FailureDetector.HEALTH_DEGRADED:
    current_status_text = "Operating via Failover"
    status_tone = "amber"
else:
    current_status_text = "All Systems Normal"
    status_tone = "green"

# Render 5 Summary Metric Cards
m_cols = st.columns(5, gap="medium")
with m_cols[0]:
    metric_card(
        "Total Clients",
        f"{total_clients} Active",
        "Simulated Endpoints (1-3)",
        "cyan"
    )
with m_cols[1]:
    metric_card(
        "Active Routers",
        active_routers_val,
        f"{net_stats['failed_routers']} offline routers",
        "green" if not net_stats['failed_routers'] else "red"
    )
with m_cols[2]:
    metric_card(
        "Network Health",
        net_health_val,
        health_info["reason"],
        health_tone
    )
with m_cols[3]:
    metric_card(
        "Active Alerts",
        str(active_alerts_count),
        f"{suspicious_or_malicious_clients} security flags",
        "green" if active_alerts_count == 0 else "red"
    )
with m_cols[4]:
    metric_card(
        "Current Network Status",
        current_status_text,
        f"Convergence: {rec_time_str}",
        status_tone
    )

# Secondary Telemetry Line
delivery_rate = (
    f"{pkt_stats['packets_delivered'] / pkt_stats['packets_sent']:.0%}"
    if pkt_stats['packets_sent']
    else "N/A"
)
st.caption(
    f"Operational Links: {manager.get_active_graph().number_of_edges()} / {net_stats['total_links']} active · "
    f"Packet Reliability: {delivery_rate} ({pkt_stats['packets_delivered']} delivered, {pkt_stats['packets_lost']} lost) · "
    f"Last Convergence Latency: {rec_time_str}"
)

# ---------------------------------------------------------
# Section 6: Visual Workflow Panel (Monitor → Detect → Validate → Block → Reroute → Recover)
# ---------------------------------------------------------
# Determine current state dynamically based on simulation conditions
healing_event = st.session_state.last_healing_event
client_under_attack = any(c.status in ("MALICIOUS", "SUSPICIOUS") for c in security_monitor.clients.values())
isolated_client = any(c.status == "ISOLATED" for c in security_monitor.clients.values())

if client_under_attack:
    workflow_cur_step = "Recover"
    workflow_msg = "An unauthorized route was attempted. Invalid route rejected & blocked before forwarding. Valid route restored via Dijkstra."
    is_step_blocked = False
elif isolated_client:
    workflow_cur_step = "Block"
    workflow_msg = "Invalid route rejected. Destination unreachable on active topology — client isolated."
    is_step_blocked = True
elif healing_event and healing_event["status"] == "RECOVERED":
    workflow_cur_step = "Recover"
    workflow_msg = f"{healing_event['failure_type']} failure detected on active path. Calculating alternative path using Dijkstra. Valid route restored successfully."
    is_step_blocked = False
elif healing_event and healing_event["status"] == "FAILED_NO_PATH":
    workflow_cur_step = "Detect"
    workflow_msg = f"Critical {healing_event['failure_type']} failure detected. All redundant paths severed — network partitioned."
    is_step_blocked = True
elif health_info["status"] == FailureDetector.HEALTH_DEGRADED:
    workflow_cur_step = "Recover"
    workflow_msg = "Network operating in degraded state. Alternative loop-free path operational."
    is_step_blocked = False
elif health_info["status"] == FailureDetector.HEALTH_DISCONNECTED:
    workflow_cur_step = "Detect"
    workflow_msg = "Router or link failure detected. Destination unreachable from source."
    is_step_blocked = True
else:
    workflow_cur_step = "Monitor"
    workflow_msg = "Network operating normally. Continuous heartbeat telemetry active across all 8 routers."
    is_step_blocked = False

workflow_stepper(workflow_cur_step, workflow_msg, is_blocked=is_step_blocked)

# ---------------------------------------------------------
# Section 3.C: Network Topology (Main Visual Focus)
# ---------------------------------------------------------
section_heading(
    "topology-workspace",
    "01",
    "Network Topology & Real-Time Telemetry Map",
    "Main visual focus: Monitor operational routers, communication paths, severed links, and blocked rogue routes."
)

# Self-Healing Incident Notification Banner
if healing_event:
    if healing_event["status"] == "RECOVERED":
        orig_nodes = " → ".join(healing_event["original_path"]) if healing_event["original_path"] else "None"
        new_nodes = " → ".join(healing_event["recovered_path"])
        st.markdown(f"""
        <div class='healing-banner-success'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;'>
                <strong style='font-size:1.05rem; color:#10b981; display:flex; align-items:center; gap:8px;'>
                    <span>⚡ Autonomous Self-Healing Triggered & Completed</span>
                </strong>
                <span style='background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#10b981; padding:3px 10px; border-radius:6px; font-weight:700; font-size:0.8rem;'>
                    RECOVERY TIME: {healing_event['recovery_time']:.3f}s
                </span>
            </div>
            <div style='font-size:0.92rem; line-height:1.7; color:#e2e8f0;'>
                • <strong>Root Cause Detected:</strong> {healing_event['failure_type']} <code>{healing_event['failed_item']}</code> compromised the active path.<br>
                • <strong>Compromised Route:</strong> <span style='text-decoration:line-through; color:#f87171;'>{orig_nodes}</span><br>
                • <strong>Alternative Shortest Path Recomputed:</strong> <strong style='color:#00e5ff;'>{new_nodes}</strong> (Total Cost: <code>{healing_event['recovered_cost']}</code>)<br>
                • <strong>Convergence Status:</strong> <span style='color:#10b981; font-weight:700;'>✓ Network Telemetry Restored with Zero System Downtime.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    elif healing_event["status"] == "FAILED_NO_PATH":
        st.markdown(f"""
        <div class='healing-banner-fail'>
            <strong style='font-size:1.05rem; color:#ef4444; display:flex; align-items:center; gap:8px; margin-bottom:8px;'>
                <span>🔴 Critical Network Partition Detected</span>
            </strong>
            <div style='font-size:0.92rem; line-height:1.6; color:#e2e8f0;'>
                • <strong>Failure Impact:</strong> {healing_event['failure_type']} <code>{healing_event['failed_item']}</code> severed the only remaining link path.<br>
                • <strong>Destination Unreachable:</strong> No alternative operational route exists between <strong>Router {st.session_state.source_router}</strong> and <strong>Router {st.session_state.dest_router}</strong>.<br>
                • <strong>NOC Action Required:</strong> Use the recovery panel to restore routers or links.
            </div>
        </div>
        """, unsafe_allow_html=True)

# Visualizer Controls Header
v_head1, v_head2, v_head3 = st.columns([1.5, 1.2, 1.0])
with v_head1:
    st.markdown('<div class="panel-title">🌐 Live Network Graph View</div>', unsafe_allow_html=True)
with v_head2:
    view_scope = st.radio(
        "Graph Scope",
        ["Full Architecture (Clients & Database)", "Core Router Mesh (A–H)"],
        horizontal=True,
        label_visibility="collapsed"
    )
with v_head3:
    viz_mode = st.selectbox(
        "Render Engine",
        options=["Interactive PyVis (WebGL)", "Static Telemetry Map"],
        label_visibility="collapsed"
    )

# Consistent Color Legend
st.markdown("""
<div class="legend">
    <span><span style="color:#10b981;">●</span> Online Router / Client</span>
    <span><span style="color:#f43f5e;">●</span> Offline Router / Blocked Node</span>
    <span><span style="color:#f59e0b;">●</span> Suspicious Activity</span>
    <span><span style="color:#00e5ff;">●</span> Active Route Node</span>
    <span><span style="color:#a855f7;">●</span> Destination Database (H)</span>
    <span><span style="color:#00e5ff; font-weight:bold;">━━</span> Active Route</span>
    <span><span style="color:#f43f5e; font-weight:bold;">┈┈</span> Severed / Blocked Link</span>
    <span><span style="color:#334155;">━━</span> Operational Link</span>
</div>
""", unsafe_allow_html=True)

# Build Graph visualization inputs
# If Full Architecture is selected, include Clients and Database H
if "Full Architecture" in view_scope:
    selected_client_key = st.session_state.get("security_client", "Client 2")
    current_sec_client = security_monitor.clients.get(selected_client_key)
    blocked_overlay = (
        current_sec_client.last_incident.get("invalid_path")
        if current_sec_client and current_sec_client.last_incident
        else None
    )
    graph_clients = list(security_monitor.clients.values())
    active_display_path = st.session_state.current_route or (current_sec_client.route if current_sec_client else None)
else:
    graph_clients = None
    blocked_overlay = None
    active_display_path = st.session_state.current_route

# Render Graph
if viz_mode == "Interactive PyVis (WebGL)":
    html_content = generate_pyvis_html(
        manager,
        active_display_path,
        height="500px",
        clients=graph_clients,
        blocked_path=blocked_overlay,
    )
    components.html(html_content, height=510, scrolling=False)
else:
    fig = generate_matplotlib_figure(
        manager,
        active_display_path,
        clients=graph_clients,
        blocked_path=blocked_overlay,
    )
    st.pyplot(fig)
    plt.close(fig)

# Active Route Stepper Pill Sequence
if active_display_path:
    pills_html = ""
    for idx, node in enumerate(active_display_path):
        node_label = f"Database ({node})" if node == "H" else f"Router {node}"
        pills_html += f"<span class='route-node-pill'>{node_label}</span>"
        if idx < len(active_display_path) - 1:
            pills_html += "<span class='route-arrow'>──►</span>"

    cost_display = st.session_state.current_cost if st.session_state.current_cost is not None else "Active"
    st.markdown(f"""
    <div class='route-stepper-box'>
        <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
            <span style='font-size:0.82rem; font-weight:700; color:#94a3b8; text-transform:uppercase;'>Active Verified Route:</span>
            <span style='font-family:monospace; font-weight:700; color:#38bdf8; background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.3); padding:2px 10px; border-radius:6px; font-size:0.82rem;'>
                Total Dijkstra Metric Cost: {cost_display} | Hops: {len(active_display_path) - 1}
            </span>
        </div>
        <div>{pills_html}</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class='route-stepper-box' style='text-align:center; padding:16px; color:#64748b;'>
        <span>💡 Select routers in <strong>Network Failure Testing</strong> or trigger client requests in <strong>Security Testing</strong> to view active routing paths.</span>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Section 7: Separate Network Failure and Security Testing Workspaces
# ---------------------------------------------------------
st.write("")
st.markdown("<hr style='border-color:rgba(30,44,64,0.7); margin:18px 0 24px 0;'>", unsafe_allow_html=True)

test_tab1, test_tab2 = st.tabs([
    "⚡ Network Failure Testing (Self-Healing)",
    "🛡️ Security Testing — Simulate a Malicious Client"
])

# =========================================================
# TAB 1: Network Failure Testing
# Demonstrates: Failure → Detection → Dijkstra → Alternative Route → Recovery
# =========================================================
with test_tab1:
    section_heading(
        "failure-workspace",
        "02A",
        "Network Failure Testing & Fault Resilience",
        "Demonstrate router and link failure injection, automated detection, Dijkstra shortest-path recalculation, and self-healing."
    )

    fail_col_left, fail_col_right = st.columns([1.3, 1.0], gap="large")

    with fail_col_left:
        st.markdown('<div class="panel-title">🎛️ Command & Control Studio</div>', unsafe_allow_html=True)
        fail_subtabs = st.tabs(["Routing & Flow", "Failure Injection", "Recovery & Reset"])

        # -----------------------------------------------------
        # SUBTAB 1: Routing & Flow
        # -----------------------------------------------------
        with fail_subtabs[0]:
            st.markdown(
                "<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:14px;'>"
                "Compute dynamic shortest paths using Dijkstra's algorithm and simulate packet delivery.</div>",
                unsafe_allow_html=True,
            )

            all_routers = sorted(list(manager.base_graph.nodes))
            r_c1, r_c2 = st.columns(2)
            with r_c1:
                source_idx = (
                    all_routers.index(st.session_state.source_router)
                    if st.session_state.source_router in all_routers
                    else 0
                )
                source_sel = st.selectbox("Source Router", options=all_routers, index=source_idx)
                st.session_state.source_router = source_sel

            with r_c2:
                dest_idx = (
                    all_routers.index(st.session_state.dest_router)
                    if st.session_state.dest_router in all_routers
                    else len(all_routers) - 1
                )
                dest_sel = st.selectbox("Destination Router", options=all_routers, index=dest_idx)
                st.session_state.dest_router = dest_sel

            st.write("")
            b_c1, b_c2 = st.columns(2, gap="small")
            with b_c1:
                find_route_btn = st.button("🔍 Find Best Route", use_container_width=True, type="primary")
            with b_c2:
                send_packet_btn = st.button("🚀 Transmit Packet", use_container_width=True)

            # Action: Find Best Route
            if find_route_btn:
                if source_sel == dest_sel:
                    st.warning("Source and Destination routers cannot be identical.")
                elif not manager.is_node_active(source_sel):
                    st.error(f"Cannot calculate route: Source Router {source_sel} is OFFLINE.")
                elif not manager.is_node_active(dest_sel):
                    st.error(f"Cannot calculate route: Destination Router {dest_sel} is OFFLINE.")
                else:
                    active_g = manager.get_active_graph()
                    path, cost, hops = find_shortest_path(active_g, source_sel, dest_sel)

                    if path is not None:
                        st.session_state.current_route = path
                        st.session_state.current_cost = cost
                        st.session_state.route_hops = hops
                        st.session_state.last_healing_event = None
                        route_str = " → ".join(path)
                        log_event(f"[ROUTE] Optimal path computed: {route_str} (Metric Cost: {cost})")
                        st.success(f"Best Route found: **{route_str}** | Total Cost: **{cost}**")
                        st.rerun()
                    else:
                        st.session_state.current_route = None
                        st.session_state.current_cost = None
                        st.session_state.route_hops = []
                        log_event(f"[ROUTE] Routing failed: No reachable path between {source_sel} and {dest_sel}")
                        st.error("No route exists between the selected routers.")
                        st.rerun()

            # Action: Send Packet
            if send_packet_btn:
                if not st.session_state.current_route:
                    st.warning("Please compute an active route first before transmitting packets.")
                else:
                    trans_result = packet_sim.transmit_packet(st.session_state.current_route, manager)
                    st.session_state.packet_logs = trans_result["hop_logs"]

                    for hop_msg in trans_result["hop_logs"]:
                        log_event(f"[PACKET] {hop_msg}")

                    if trans_result["success"]:
                        st.toast("Packet successfully delivered to destination!", icon="✔")
                    else:
                        st.toast("Packet transmission failed: Packet dropped in transit!", icon="❌")
                    st.rerun()

        # -----------------------------------------------------
        # SUBTAB 2: Failure Injection Studio
        # -----------------------------------------------------
        with fail_subtabs[1]:
            st.markdown(
                "<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:14px;'>"
                "Simulate physical link severance or router hardware crashes to test self-healing.</div>",
                unsafe_allow_html=True,
            )

            fail_type = st.radio("Select Failure Domain", ["Sever Network Link", "Crash Router Node"], horizontal=True)

            if fail_type == "Sever Network Link":
                active_links = manager.get_active_links()
                link_options = [f"{u} - {v}" for u, v in active_links]

                if not link_options:
                    st.info("All network links are currently severed.")
                else:
                    selected_link_str = st.selectbox("Select Active Link to Sever", options=link_options)
                    fail_link_btn = st.button("💥 Sever Link", use_container_width=True)

                    if fail_link_btn and selected_link_str:
                        u, v = selected_link_str.split(" - ")
                        if manager.fail_link(u, v):
                            st.session_state.monitoring_banner = f"Fault detected: Link {u} <-> {v} severed."
                            log_event(f"[FAIL] Link {u}-{v} severed")
                            log_event(f"[MONITOR] Failure detected: Link {u} <-> {v}")

                            # Trigger Self-Healing
                            if st.session_state.current_route:
                                log_event("[HEAL] MeshGuard initiating autonomous reroute...")
                                healing_res = SelfHealingEngine.trigger_healing(
                                    manager=manager,
                                    source=st.session_state.source_router,
                                    destination=st.session_state.dest_router,
                                    current_path=st.session_state.current_route,
                                    failure_type="Link",
                                    failed_item=f"{u}-{v}",
                                )
                                st.session_state.last_healing_event = healing_res
                                st.session_state.last_recovery_time = healing_res["recovery_time"]

                                if healing_res["status"] == "RECOVERED":
                                    st.session_state.current_route = healing_res["recovered_path"]
                                    st.session_state.current_cost = healing_res["recovered_cost"]
                                    st.session_state.route_hops = healing_res["hops_detail"]
                                    new_r_str = " → ".join(healing_res["recovered_path"])
                                    log_event(f"[HEAL] Alternative route established: {new_r_str}")
                                    log_event(f"[HEAL] Network recovered in {healing_res['recovery_time']:.3f}s")
                                elif healing_res["status"] == "FAILED_NO_PATH":
                                    st.session_state.current_route = None
                                    st.session_state.current_cost = None
                                    st.session_state.route_hops = []
                                    log_event("[FAIL] Network could not recover: Partitioned graph.")
                            st.rerun()

            else:
                active_routers = manager.get_active_nodes()
                if not active_routers:
                    st.info("All routers are currently down.")
                else:
                    selected_router = st.selectbox("Select Router to Crash", options=active_routers)
                    fail_router_btn = st.button("🛑 Crash Router", use_container_width=True)

                    if fail_router_btn and selected_router:
                        if manager.fail_node(selected_router):
                            st.session_state.monitoring_banner = f"Fault detected: Router {selected_router} offline."
                            log_event(f"[FAIL] Router {selected_router} hardware crash")
                            log_event(f"[FAIL] All links connected to Router {selected_router} disabled")

                            # Trigger Self-Healing
                            if st.session_state.current_route:
                                log_event("[HEAL] MeshGuard initiating autonomous reroute...")
                                healing_res = SelfHealingEngine.trigger_healing(
                                    manager=manager,
                                    source=st.session_state.source_router,
                                    destination=st.session_state.dest_router,
                                    current_path=st.session_state.current_route,
                                    failure_type="Router",
                                    failed_item=selected_router,
                                )
                                st.session_state.last_healing_event = healing_res
                                st.session_state.last_recovery_time = healing_res["recovery_time"]

                                if healing_res["status"] == "RECOVERED":
                                    st.session_state.current_route = healing_res["recovered_path"]
                                    st.session_state.current_cost = healing_res["recovered_cost"]
                                    st.session_state.route_hops = healing_res["hops_detail"]
                                    new_r_str = " → ".join(healing_res["recovered_path"])
                                    log_event(f"[HEAL] Alternative route established: {new_r_str}")
                                    log_event(f"[HEAL] Network recovered in {healing_res['recovery_time']:.3f}s")
                                elif healing_res["status"] == "FAILED_NO_PATH":
                                    st.session_state.current_route = None
                                    st.session_state.current_cost = None
                                    st.session_state.route_hops = []
                                    log_event("[FAIL] Network could not recover: Partitioned graph.")
                            st.rerun()

        # -----------------------------------------------------
        # SUBTAB 3: Recovery & Reset
        # -----------------------------------------------------
        with fail_subtabs[2]:
            st.markdown(
                "<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:14px;'>"
                "Re-enable failed links, power up crashed routers, or restore pristine default topology.</div>",
                unsafe_allow_html=True,
            )

            r_subtab1, r_subtab2 = st.tabs(["Restore Link", "Restore Router"])

            with r_subtab1:
                failed_links = manager.get_failed_links()
                if not failed_links:
                    st.success("All links are operational.", icon="✔")
                else:
                    f_link_opts = [f"{u} - {v}" for u, v in failed_links]
                    sel_f_link = st.selectbox("Failed Link to Restore", options=f_link_opts)
                    rest_link_btn = st.button("🔄 Restore Selected Link", use_container_width=True)

                    if rest_link_btn and sel_f_link:
                        u, v = sel_f_link.split(" - ")
                        if manager.restore_link(u, v):
                            log_event(f"[RESTORE] Link {u}-{v} restored to ACTIVE")
                            st.session_state.monitoring_banner = f"Link {u}-{v} restored."

                            if manager.is_node_active(st.session_state.source_router) and manager.is_node_active(
                                st.session_state.dest_router
                            ):
                                act_g = manager.get_active_graph()
                                p, c, h = find_shortest_path(
                                    act_g, st.session_state.source_router, st.session_state.dest_router
                                )
                                if p:
                                    st.session_state.current_route = p
                                    st.session_state.current_cost = c
                                    st.session_state.route_hops = h
                                    log_event(f"[ROUTE] Optimal route updated: {' → '.join(p)} (Cost: {c})")
                            st.rerun()

            with r_subtab2:
                failed_routers = manager.get_failed_nodes()
                if not failed_routers:
                    st.success("All routers are online.", icon="✔")
                else:
                    sel_f_router = st.selectbox("Failed Router to Restore", options=failed_routers)
                    rest_router_btn = st.button("🔄 Restore Selected Router", use_container_width=True)

                    if rest_router_btn and sel_f_router:
                        if manager.restore_node(sel_f_router):
                            log_event(f"[RESTORE] Router {sel_f_router} powered up and ONLINE")
                            st.session_state.monitoring_banner = f"Router {sel_f_router} restored."

                            if manager.is_node_active(st.session_state.source_router) and manager.is_node_active(
                                st.session_state.dest_router
                            ):
                                act_g = manager.get_active_graph()
                                p, c, h = find_shortest_path(
                                    act_g, st.session_state.source_router, st.session_state.dest_router
                                )
                                if p:
                                    st.session_state.current_route = p
                                    st.session_state.current_cost = c
                                    st.session_state.route_hops = h
                                    log_event(f"[ROUTE] Optimal route updated: {' → '.join(p)} (Cost: {c})")
                            st.rerun()

            st.write("")
            st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin:12px 0;'>", unsafe_allow_html=True)
            reset_network_btn = st.button("♻ Reset Entire Network", use_container_width=True)
            if reset_network_btn:
                manager.reset_network()
                packet_sim.reset_metrics()
                st.session_state.security_monitor = SecurityMonitor(manager, packet_sim, event_sink=log_event)
                st.session_state.current_route = None
                st.session_state.current_cost = None
                st.session_state.route_hops = []
                st.session_state.last_healing_event = None
                st.session_state.last_recovery_time = None
                st.session_state.packet_logs = []
                st.session_state.monitoring_banner = "Network reset to default state. All routers and links active."
                log_event("[RESET] Network topology reset to default state")
                st.rerun()

    with fail_col_right:
        st.markdown('<div class="panel-title">📋 Route Breakdown & Hop Telemetry</div>', unsafe_allow_html=True)
        if st.session_state.route_hops:
            st.dataframe(
                st.session_state.route_hops,
                column_config={
                    "hop": "Hop #",
                    "from": "From Router",
                    "to": "To Router",
                    "link": "Link Adjacency",
                    "cost": "Metric Cost",
                    "cumulative_cost": "Total Path Cost",
                },
                hide_index=True,
                use_container_width=True,
            )
        else:
            st.info("No active route computed. Use 'Find Best Route' to display telemetry.")

        if st.session_state.packet_logs:
            st.markdown(
                "<h5 style='color:#e2e8f0; margin-top:16px; margin-bottom:8px;'>📦 Virtual Packet Telemetry Flow</h5>",
                unsafe_allow_html=True,
            )
            pkt_box_html = ""
            for plog in st.session_state.packet_logs:
                if "[OK]" in plog:
                    pkt_box_html += f"<div style='color:#10b981; font-weight:600;'>{plog}</div>"
                elif "[FAIL]" in plog or "dropped" in plog:
                    pkt_box_html += f"<div style='color:#f43f5e; font-weight:600;'>{plog}</div>"
                else:
                    pkt_box_html += f"<div style='color:#38bdf8;'>{plog}</div>"
            st.markdown(
                f"<div style='background:#080c14; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 16px; font-family:monospace; font-size:0.82rem; line-height:1.5;'>{pkt_box_html}</div>",
                unsafe_allow_html=True,
            )


# =========================================================
# TAB 2: Security Testing — Simulate a Malicious Client
# Demonstrates: Malicious Client Simulation → Route Validation → Invalid Route Rejection → Safe Route Selection → Recovery
# =========================================================
with test_tab2:
    render_security_monitor(security_monitor, viz_mode)


# ---------------------------------------------------------
# Section 8: Unified & Filterable Event Logs
# ---------------------------------------------------------
st.write("")
st.markdown("<hr style='border-color:rgba(30,44,64,0.7); margin:24px 0 18px 0;'>", unsafe_allow_html=True)
section_heading(
    "logs-workspace",
    "03",
    "Network Audit & Event Logs",
    "Real-time synchronized event logs detailing routing calculations, equipment outages, security rejections, and autonomous recovery."
)

log_ctrl1, log_ctrl2 = st.columns([1.2, 2.0], gap="medium")
with log_ctrl1:
    severity_filter = st.selectbox(
        "Filter by Severity",
        ["All Severities", "SECURITY ALERT", "ERROR", "WARNING", "INFO"],
        index=0,
    )
with log_ctrl2:
    keyword_filter = st.text_input(
        "Search Audit Logs",
        placeholder="Filter by keyword (e.g., Client 2, Link D-F, Dijkstra)...",
    )

raw_logs = list(reversed(st.session_state.event_logs[-100:]))
parsed_logs = [parse_log_entry(entry) for entry in raw_logs]

# Apply Filters
filtered_logs = []
for item in parsed_logs:
    if severity_filter != "All Severities" and item["severity"] != severity_filter:
        continue
    if keyword_filter and keyword_filter.lower() not in item["raw"].lower():
        continue
    filtered_logs.append(item)

if not st.session_state.event_logs:
    st.info("No event logs recorded yet.")
elif not filtered_logs:
    st.warning("No log events match the selected filter criteria.")
else:
    # Display formatted table
    table_data = [
        {
            "Timestamp": item["timestamp"],
            "Severity": item["severity"],
            "Affected Component": item["affected"],
            "Event Description": item["event"],
            "Action Taken": item["action"],
        }
        for item in filtered_logs[:40]
    ]
    st.dataframe(
        table_data,
        column_config={
            "Timestamp": st.column_config.TextColumn("Timestamp", width="small"),
            "Severity": st.column_config.TextColumn("Severity", width="medium"),
            "Affected Component": st.column_config.TextColumn("Affected Entity", width="medium"),
            "Event Description": st.column_config.TextColumn("Event Description", width="large"),
            "Action Taken": st.column_config.TextColumn("Action Taken", width="medium"),
        },
        hide_index=True,
        use_container_width=True,
    )

# Optional Terminal View Expander
with st.expander("🖥️ Live NOC Telemetry Terminal Console (Raw Output)", expanded=False):
    visible_logs = st.session_state.event_logs[-35:]
    formatted_lines = []
    for log_l in visible_logs:
        if "[FAIL]" in log_l:
            formatted_lines.append(f"<span style='color:#f43f5e;'>{log_l}</span>")
        elif "[HEAL]" in log_l:
            formatted_lines.append(f"<span style='color:#10b981; font-weight:600;'>{log_l}</span>")
        elif "[SECURITY]" in log_l:
            formatted_lines.append(f"<span style='color:#fb7185; font-weight:600;'>{log_l}</span>")
        elif "[ROUTE]" in log_l:
            formatted_lines.append(f"<span style='color:#38bdf8;'>{log_l}</span>")
        elif "[RESTORE]" in log_l:
            formatted_lines.append(f"<span style='color:#a78bfa;'>{log_l}</span>")
        elif "[PACKET]" in log_l:
            formatted_lines.append(f"<span style='color:#fbbf24;'>{log_l}</span>")
        else:
            formatted_lines.append(f"<span style='color:#94a3b8;'>{log_l}</span>")

    log_body = "<br>".join(formatted_lines)
    st.markdown(f"""
    <div class='terminal-window'>
        <div class='terminal-titlebar'>
            <span class='terminal-dot t-red'></span>
            <span class='terminal-dot t-yellow'></span>
            <span class='terminal-dot t-green'></span>
            <span class='terminal-text'>meshguard@telemetry-daemon: ~ / live-events</span>
        </div>
        <div class='terminal-body'>{log_body}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Footer
# ---------------------------------------------------------
st.markdown("""
<footer class="workspace-footer">
    <span>MESHGUARD · SECURE SELF-HEALING NETWORK SIMULATOR</span>
    <span>Autonomous Failure Recovery & Route Security · College Project Demonstration</span>
</footer>
""", unsafe_allow_html=True)
