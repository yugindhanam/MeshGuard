"""
app.py - MeshGuard: Self-Healing Computer Network Simulator
Advanced Cyber NOC Edition - High-Tech Network Telemetry & Self-Healing Simulator
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
    initial_sidebar_state="collapsed"
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
    entry = f"[{timestamp}] {message}"
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

# ---------------------------------------------------------
# Cyber NOC Design System CSS
# ---------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

    /* Global Dark Theme Overrides */
    .stApp {
        background: radial-gradient(circle at 50% 0%, #131b2e 0%, #0b0f19 75%, #070a12 100%);
        color: #f1f5f9;
        font-family: 'Inter', -apple-system, sans-serif;
    }

    /* Top Navigation Header */
    .noc-header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(56, 189, 248, 0.15);
        border-radius: 14px;
        padding: 16px 24px;
        margin-bottom: 20px;
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }
    .brand-title {
        font-size: 1.85rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .brand-subtitle {
        font-size: 0.85rem;
        font-weight: 500;
        color: #94a3b8;
        letter-spacing: 0.2px;
        margin-top: 2px;
    }

    /* Status Badges with Pulse */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 8px;
        padding: 8px 18px;
        border-radius: 9999px;
        font-weight: 700;
        font-size: 0.88rem;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }
    .pill-healthy {
        background: rgba(16, 185, 129, 0.15);
        color: #10b981;
        border: 1px solid rgba(16, 185, 129, 0.4);
        box-shadow: 0 0 16px rgba(16, 185, 129, 0.25);
    }
    .pill-degraded {
        background: rgba(245, 158, 11, 0.15);
        color: #f59e0b;
        border: 1px solid rgba(245, 158, 11, 0.4);
        box-shadow: 0 0 16px rgba(245, 158, 11, 0.25);
    }
    .pill-disconnected {
        background: rgba(239, 68, 68, 0.15);
        color: #ef4444;
        border: 1px solid rgba(239, 68, 68, 0.4);
        box-shadow: 0 0 16px rgba(239, 68, 68, 0.35);
    }

    /* Live Beacon Indicator */
    .pulse-dot {
        width: 9px;
        height: 9px;
        border-radius: 50%;
        display: inline-block;
        animation: pulseAnimation 1.8s infinite;
    }
    .dot-green { background: #10b981; box-shadow: 0 0 8px #10b981; }
    .dot-amber { background: #f59e0b; box-shadow: 0 0 8px #f59e0b; }
    .dot-red { background: #ef4444; box-shadow: 0 0 8px #ef4444; }

    @keyframes pulseAnimation {
        0% { transform: scale(0.95); opacity: 0.8; }
        50% { transform: scale(1.3); opacity: 1; }
        100% { transform: scale(0.95); opacity: 0.8; }
    }

    /* Telemetry KPI Cards */
    .kpi-card {
        background: rgba(15, 23, 42, 0.7);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 20px -5px rgba(0, 0, 0, 0.4);
        position: relative;
        overflow: hidden;
    }
    .kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 2px;
        background: linear-gradient(90deg, #38bdf8, #818cf8);
    }
    .kpi-card-header {
        font-size: 0.78rem;
        font-weight: 600;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 8px;
    }
    .kpi-card-value {
        font-size: 1.75rem;
        font-weight: 800;
        color: #f8fafc;
        font-family: 'JetBrains Mono', monospace;
    }
    .kpi-card-sub {
        font-size: 0.8rem;
        color: #64748b;
        margin-top: 4px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    /* Glass Control Panel Box */
    .control-card {
        background: rgba(15, 23, 42, 0.65);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 18px;
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.35);
    }

    /* Self-Healing Callout Banner */
    .healing-banner-success {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 95, 70, 0.18) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-left: 5px solid #10b981;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 25px -5px rgba(16, 185, 129, 0.2);
    }
    .healing-banner-fail {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.12) 0%, rgba(153, 27, 27, 0.18) 100%);
        border: 1px solid rgba(239, 68, 68, 0.4);
        border-left: 5px solid #ef4444;
        border-radius: 10px;
        padding: 16px 20px;
        margin-bottom: 20px;
        box-shadow: 0 8px 25px -5px rgba(239, 68, 68, 0.2);
    }

    /* Active Route Breadcrumb Display */
    .route-stepper-box {
        background: rgba(11, 15, 25, 0.85);
        border: 1px solid rgba(56, 189, 248, 0.3);
        border-radius: 10px;
        padding: 14px 18px;
        margin-top: 10px;
        box-shadow: inset 0 2px 8px rgba(0, 0, 0, 0.4);
    }
    .route-node-pill {
        display: inline-block;
        background: #0284c7;
        color: #ffffff;
        font-family: 'JetBrains Mono', monospace;
        font-weight: 700;
        font-size: 0.88rem;
        padding: 4px 12px;
        border-radius: 6px;
        box-shadow: 0 2px 8px rgba(2, 132, 199, 0.4);
    }
    .route-arrow {
        color: #38bdf8;
        font-weight: 700;
        margin: 0 6px;
    }

    /* Terminal Console Window */
    .terminal-window {
        background: #080c14;
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
    }
    .terminal-titlebar {
        background: #0f172a;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        padding: 8px 14px;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .terminal-dot {
        width: 11px;
        height: 11px;
        border-radius: 50%;
        display: inline-block;
    }
    .t-red { background: #ff5f56; }
    .t-yellow { background: #ffbd2e; }
    .t-green { background: #27c93f; }
    .terminal-text {
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        color: #94a3b8;
        margin-left: 8px;
    }
    .terminal-body {
        padding: 14px 18px;
        height: 250px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        line-height: 1.6;
        color: #38bdf8;
        background: #080c14;
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
# Top Navigation Header Banner
# ---------------------------------------------------------
status_class = "pill-healthy"
pulse_class = "dot-green"
if health_info["status"] == FailureDetector.HEALTH_DEGRADED:
    status_class = "pill-degraded"
    pulse_class = "dot-amber"
elif health_info["status"] == FailureDetector.HEALTH_DISCONNECTED:
    status_class = "pill-disconnected"
    pulse_class = "dot-red"

st.markdown(f"""
<div class='noc-header-container'>
    <div>
        <div class='brand-title'>
            <span>🛡️ MeshGuard</span>
            <span style='font-size:0.95rem; font-weight:600; color:#38bdf8; border:1px solid rgba(56,189,248,0.4); padding:2px 8px; border-radius:6px;'>v2.0 NOC</span>
        </div>
        <div class='brand-subtitle'>Self-Healing Dynamic Routing Protocol & Network Fault Recovery Simulator</div>
    </div>
    <div style='display:flex; align-items:center; gap:16px;'>
        <div class='status-pill {status_class}'>
            <span class='pulse-dot {pulse_class}'></span>
            {health_info['badge']}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Telemetry KPI Dashboard Cards
# ---------------------------------------------------------
net_stats = manager.get_statistics()
pkt_stats = packet_sim.get_stats()
rec_time_str = f"{st.session_state.last_recovery_time:.3f} s" if st.session_state.last_recovery_time is not None else "0.000 s"

delivery_rate = 100.0
if pkt_stats["packets_sent"] > 0:
    delivery_rate = round((pkt_stats["packets_delivered"] / pkt_stats["packets_sent"]) * 100, 1)

kpi_c1, kpi_c2, kpi_c3 = st.columns(3, gap="medium")

with kpi_c1:
    router_status_color = "#10b981" if net_stats["failed_routers"] == 0 else "#f43f5e"
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-card-header'>
            <span>🖥️ Router Infrastructure</span>
            <span style='color:{router_status_color}; font-weight:700;'>{net_stats["active_routers"]}/{net_stats["total_routers"]} ONLINE</span>
        </div>
        <div class='kpi-card-value'>
            {net_stats["active_routers"]} <span style='font-size:1rem; color:#64748b; font-weight:500;'>/ {net_stats["total_routers"]} Active</span>
        </div>
        <div class='kpi-card-sub'>
            <span>🔴 Failed Routers: <strong style='color:{router_status_color};'>{net_stats["failed_routers"]}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c2:
    link_status_color = "#10b981" if net_stats["failed_links"] == 0 else "#f43f5e"
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-card-header'>
            <span>🔗 Mesh Link Adjacency</span>
            <span style='color:{link_status_color}; font-weight:700;'>{net_stats["active_links"]}/{net_stats["total_links"]} ACTIVE</span>
        </div>
        <div class='kpi-card-value'>
            {net_stats["active_links"]} <span style='font-size:1rem; color:#64748b; font-weight:500;'>/ {net_stats["total_links"]} Links</span>
        </div>
        <div class='kpi-card-sub'>
            <span>⚡ Severed Links: <strong style='color:{link_status_color};'>{net_stats["failed_links"]}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

with kpi_c3:
    st.markdown(f"""
    <div class='kpi-card'>
        <div class='kpi-card-header'>
            <span>📦 Telemetry & Convergence</span>
            <span style='color:#38bdf8; font-weight:700;'>{delivery_rate}% RELIABILITY</span>
        </div>
        <div class='kpi-card-value'>
            {pkt_stats["packets_delivered"]} <span style='font-size:1rem; color:#64748b; font-weight:500;'>pkts ({pkt_stats["packets_lost"]} lost)</span>
        </div>
        <div class='kpi-card-sub'>
            <span>⚡ Last Recovery Latency: <strong style='color:#38bdf8;'>{rec_time_str}</strong></span>
        </div>
    </div>
    """, unsafe_allow_html=True)

st.write("")

# ---------------------------------------------------------
# Self-Healing Incident Notification Banner
# ---------------------------------------------------------
healing_event = st.session_state.last_healing_event
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

# ---------------------------------------------------------
# Main Two-Column Layout
# ---------------------------------------------------------
left_col, right_col = st.columns([1.35, 1.0], gap="large")

# =========================================================
# LEFT COLUMN: Network Visualization & Route Details
# =========================================================
with left_col:
    v_head1, v_head2 = st.columns([2, 1])
    with v_head1:
        st.markdown("<h4 style='margin:0; color:#f8fafc;'>🌐 Live Mesh Topology Canvas</h4>", unsafe_allow_html=True)
    with v_head2:
        viz_mode = st.selectbox(
            "Render Engine",
            options=["Interactive PyVis (WebGL)", "Static Telemetry Map"],
            label_visibility="collapsed"
        )

    # Topology Status Legend
    st.markdown("""
    <div style='display:flex; gap:16px; font-size:0.8rem; color:#94a3b8; background:rgba(15,23,42,0.5); padding:8px 14px; border-radius:8px; margin:8px 0 12px 0; border:1px solid rgba(255,255,255,0.06);'>
        <span><span style='color:#10b981;'>●</span> Online Router</span>
        <span><span style='color:#f43f5e;'>●</span> Offline Router</span>
        <span><span style='color:#00e5ff;'>●</span> Route Node</span>
        <span><span style='color:#00e5ff;'>━━</span> Active Route</span>
        <span><span style='color:#f43f5e;'>┈</span> Severed Link</span>
    </div>
    """, unsafe_allow_html=True)

    # Render Visualizer
    if viz_mode == "Interactive PyVis (WebGL)":
        html_content = generate_pyvis_html(manager, st.session_state.current_route, height="490px")
        components.html(html_content, height=500, scrolling=False)
    else:
        fig = generate_matplotlib_figure(manager, st.session_state.current_route)
        st.pyplot(fig)
        plt.close(fig)

    # Active Route Stepper & Cost Pill
    if st.session_state.current_route:
        route_nodes = st.session_state.current_route
        pills_html = ""
        for idx, node in enumerate(route_nodes):
            pills_html += f"<span class='route-node-pill'>Router {node}</span>"
            if idx < len(route_nodes) - 1:
                pills_html += "<span class='route-arrow'>──►</span>"

        st.markdown(f"""
        <div class='route-stepper-box'>
            <div style='display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;'>
                <span style='font-size:0.82rem; font-weight:700; color:#94a3b8; text-transform:uppercase;'>Active Routing Path:</span>
                <span style='font-family:monospace; font-weight:700; color:#38bdf8; background:rgba(56,189,248,0.15); border:1px solid rgba(56,189,248,0.3); padding:2px 10px; border-radius:6px; font-size:0.82rem;'>
                    Total Metric Cost: {st.session_state.current_cost} | Hops: {len(route_nodes) - 1}
                </span>
            </div>
            <div>{pills_html}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='route-stepper-box' style='text-align:center; padding:18px; color:#64748b;'>
            <span>💡 Select a Source and Destination router on the right, then click <strong>Calculate Optimal Route</strong>.</span>
        </div>
        """, unsafe_allow_html=True)

    # Packet Transmission Feed
    if st.session_state.packet_logs:
        st.markdown("<h5 style='color:#e2e8f0; margin-top:16px; margin-bottom:8px;'>📦 Virtual Packet Telemetry Flow</h5>", unsafe_allow_html=True)
        pkt_box_html = ""
        for plog in st.session_state.packet_logs:
            if "[OK]" in plog:
                pkt_box_html += f"<div style='color:#10b981; font-weight:600;'>{plog}</div>"
            elif "[FAIL]" in plog or "dropped" in plog:
                pkt_box_html += f"<div style='color:#f43f5e; font-weight:600;'>{plog}</div>"
            else:
                pkt_box_html += f"<div style='color:#38bdf8;'>{plog}</div>"
        st.markdown(f"<div style='background:#080c14; border:1px solid rgba(255,255,255,0.08); border-radius:8px; padding:12px 16px; font-family:monospace; font-size:0.82rem; line-height:1.5;'>{pkt_box_html}</div>", unsafe_allow_html=True)


# =========================================================
# RIGHT COLUMN: Command & Control Center
# =========================================================
with right_col:
    st.markdown("<h4 style='margin:0; color:#f8fafc; margin-bottom:12px;'>🎮 NOC Command & Control</h4>", unsafe_allow_html=True)

    main_tabs = st.tabs(["🧭 Routing & Flow", "⚡ Failure Injection", "🔧 Recovery & Reset"])

    # -----------------------------------------------------
    # TAB 1: Routing & Flow
    # -----------------------------------------------------
    with main_tabs[0]:
        st.markdown("<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:14px;'>Compute dynamic shortest paths using Dijkstra's algorithm and simulate packet delivery.</div>", unsafe_allow_html=True)

        all_routers = sorted(list(manager.base_graph.nodes))
        r_c1, r_c2 = st.columns(2)
        with r_c1:
            source_idx = all_routers.index(st.session_state.source_router) if st.session_state.source_router in all_routers else 0
            source_sel = st.selectbox("Source Router", options=all_routers, index=source_idx)
            st.session_state.source_router = source_sel

        with r_c2:
            dest_idx = all_routers.index(st.session_state.dest_router) if st.session_state.dest_router in all_routers else len(all_routers) - 1
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
    # TAB 2: Failure Injection Studio
    # -----------------------------------------------------
    with main_tabs[1]:
        st.markdown("<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:14px;'>Simulate physical link severance or router hardware crashes to test self-healing.</div>", unsafe_allow_html=True)

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
                                failed_item=f"{u}-{v}"
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
                                failed_item=selected_router
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
    # TAB 3: Recovery & Reset
    # -----------------------------------------------------
    with main_tabs[2]:
        st.markdown("<div style='font-size:0.85rem; color:#94a3b8; margin-bottom:14px;'>Re-enable failed links, power up crashed routers, or restore pristine default topology.</div>", unsafe_allow_html=True)

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

                        if manager.is_node_active(st.session_state.source_router) and manager.is_node_active(st.session_state.dest_router):
                            act_g = manager.get_active_graph()
                            p, c, h = find_shortest_path(act_g, st.session_state.source_router, st.session_state.dest_router)
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

                        if manager.is_node_active(st.session_state.source_router) and manager.is_node_active(st.session_state.dest_router):
                            act_g = manager.get_active_graph()
                            p, c, h = find_shortest_path(act_g, st.session_state.source_router, st.session_state.dest_router)
                            if p:
                                st.session_state.current_route = p
                                st.session_state.current_cost = c
                                st.session_state.route_hops = h
                                log_event(f"[ROUTE] Optimal route updated: {' → '.join(p)} (Cost: {c})")
                        st.rerun()

        st.write("")
        st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin:12px 0;'>", unsafe_allow_html=True)
        reset_network_btn = st.button("♻ Reset Entire Network to Default", use_container_width=True)
        if reset_network_btn:
            manager.reset_network()
            packet_sim.reset_metrics()
            st.session_state.current_route = None
            st.session_state.current_cost = None
            st.session_state.route_hops = []
            st.session_state.last_healing_event = None
            st.session_state.last_recovery_time = None
            st.session_state.packet_logs = []
            st.session_state.monitoring_banner = "Network reset to default state. All routers and links active."
            log_event("[RESET] Network topology reset to default state")
            st.rerun()

# ---------------------------------------------------------
# SECTION 4: Live Event Logs Terminal & Hop Breakdown Table
# ---------------------------------------------------------
st.markdown("<hr style='border-color:rgba(255,255,255,0.08); margin:28px 0 20px 0;'>", unsafe_allow_html=True)
bot_c1, bot_c2 = st.columns([1.35, 1.0], gap="large")

with bot_c1:
    st.markdown("<h4 style='color:#f8fafc; margin-bottom:10px;'>📜 Live NOC Audit Console</h4>", unsafe_allow_html=True)
    visible_logs = st.session_state.event_logs[-30:]

    formatted_lines = []
    for log_l in visible_logs:
        if "[FAIL]" in log_l:
            formatted_lines.append(f"<span style='color:#f43f5e;'>{log_l}</span>")
        elif "[HEAL]" in log_l:
            formatted_lines.append(f"<span style='color:#10b981; font-weight:600;'>{log_l}</span>")
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

with bot_c2:
    st.markdown("<h4 style='color:#f8fafc; margin-bottom:10px;'>📊 Hop-by-Hop Route Breakdown</h4>", unsafe_allow_html=True)
    if st.session_state.route_hops:
        st.dataframe(
            st.session_state.route_hops,
            column_config={
                "hop": "Hop #",
                "from": "From Router",
                "to": "To Router",
                "link": "Link Adjacency",
                "cost": "Metric Cost",
                "cumulative_cost": "Total Path Cost"
            },
            hide_index=True,
            use_container_width=True
        )
    else:
        st.info("No active route computed. Use 'Find Best Route' to display telemetry.")
