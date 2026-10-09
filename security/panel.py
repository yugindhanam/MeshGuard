"""
security/panel.py - Security Testing Dashboard & Malicious Client Simulator Panel
Streamlit presentation layer for route enforcement, threat detection, and safe recovery.
"""

from html import escape
from typing import List, Optional, Dict, Any

import streamlit as st

from ui.components import section_heading, client_telemetry_table, terminology_guide
from .monitor import SecurityMonitor
from .threat_detector import ClientState


def format_route(path: Optional[List[str]]) -> str:
    """Formats a node path list into an arrow-separated string."""
    return " → ".join(path) if path else "No safe route"


def calculate_client_telemetry(monitor: SecurityMonitor, client: ClientState) -> Dict[str, Any]:
    """Calculates client route metrics honestly from graph topology without inventing physical RTT."""
    if client.route and len(client.route) > 1:
        graph = monitor.manager.base_graph
        cost = sum(
            graph[u][v].get("weight", 1)
            for u, v in zip(client.route, client.route[1:])
            if graph.has_edge(u, v)
        )
        hops = len(client.route) - 1
        cost_str = f"Cost: {cost}"
        hops_str = f"{hops} Hops"
        node_status = "Online"
    else:
        cost_str = "No Route (∞)"
        hops_str = "N/A"
        node_status = "Isolated"

    return {
        "name": client.client_id,
        "path": format_route(client.route),
        "rtt": cost_str,
        "drift": hops_str,
        "status": node_status,
        "security": client.status,
        "trust_score": client.trust_score,
        "delivered": client.delivered,
        "blocked": client.blocked_requests,
        "last_request": client.last_request,
    }


def render_client_card(client: ClientState, selected: bool) -> None:
    """Renders an individual client trust and telemetry card."""
    tone = "healthy" if client.route else "disconnected"
    if client.status in ("SUSPICIOUS", "MALICIOUS"):
        tone = "degraded" if client.status == "SUSPICIOUS" else "disconnected"
    score = max(0, min(100, client.trust_score))
    score_color = "#10b981" if score >= 80 else "#f59e0b" if score >= 50 else "#f43f5e"

    st.markdown(
        f'<article class="client-card {"is-selected" if selected else ""}">'
        f'<div class="client-card-head">'
        f'<span class="client-name">{escape(client.client_id)}</span>'
        f'<span class="status-pill pill-{tone}"><span class="pulse-dot"></span>{escape(client.status)}</span>'
        f'</div>'
        f'<div class="client-score"><span>Reputation Trust Score</span><strong>{score}<small> / 100</small></strong></div>'
        f'<div class="trust-track" role="meter" aria-label="Trust score" aria-valuemin="0" aria-valuemax="100" '
        f'aria-valuenow="{score}"><div class="trust-fill" style="width:{score}%;background:{score_color}"></div></div>'
        f'<div class="client-stats">'
        f'<span><b>{client.delivered}</b> delivered</span>'
        f'<span><b>{client.blocked_requests}</b> blocked</span>'
        f'</div>'
        f'<div class="client-route">{escape(format_route(client.route))}</div>'
        f'<div class="client-result">{escape(client.last_request)}</div>'
        f'</article>',
        unsafe_allow_html=True,
    )


def render_incident_walkthrough(client: ClientState) -> None:
    """
    Renders the 7-step guided incident and route validation walkthrough:
    1. Original route
    2. Invalid route attempt
    3. Route validation
    4. Security alert
    5. Route rejection
    6. Dijkstra safe alternative
    7. Recovered route & delivery
    """
    incident = client.last_incident
    st.markdown('<div class="panel-title">🛡️ Security Incident & Route Validation Walkthrough</div>', unsafe_allow_html=True)

    if not incident:
        st.markdown(f"""
        <div style="background:#0c1422; border:1px solid #1e3550; border-radius:10px; padding:18px 20px; color:#cbd5e1;">
            <div style="display:flex; align-items:center; gap:8px; margin-bottom:8px;">
                <span style="color:#10b981; font-size:16px;">✓</span>
                <strong style="color:#f1f5f9; font-size:14px;">No Active Security Violations for {escape(client.client_id)}</strong>
            </div>
            <p style="margin:0 0 10px 0; font-size:12.5px; color:#94a3b8; line-height:1.5;">
                All database requests from this client are strictly validated prior to forwarding.
                Click <strong>Simulate Malicious Route</strong> above to trigger an invalid path and watch real-time detection, rejection, and Dijkstra self-healing.
            </p>
            <div style="font-size:11.5px; color:#64748b; font-family:Consolas,monospace;">
                Validation Pipeline: 1. Verify Nodes & Edges → 2. Block Rogue Hops → 3. Recalculate Safe Dijkstra Path → 4. Safe Delivery
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    # When incident exists
    classification = incident.get("classification", "MALICIOUS")
    reasons = incident.get("reasons", [])
    safe_path = incident.get("safe_path")
    delivered = incident.get("delivered", False)

    st.markdown(f"""
    <div class="incident-header">
        <div>
            <h3 style="display:flex; align-items:center; gap:8px;">
                <span>🚨 Unauthorized Route Detected & Rejected</span>
            </h3>
            <small>{escape(client.client_id)} · Real-Time Threat Mitigation Audit</small>
        </div>
        <span class="badge-tag badge-malicious">{escape(classification)} ROUTE BLOCKED</span>
    </div>
    """, unsafe_allow_html=True)

    # 4-stage visual flow
    steps = [
        ("01 Detected", "Abnormal route proposal", "blocked"),
        ("02 Validated", "Policy rules violated", "blocked"),
        ("03 Blocked", "Zero packets forwarded", "blocked"),
        ("04 Recovered" if safe_path else "Isolated", "Trusted Dijkstra path" if safe_path else "No safe path", "" if safe_path else "pending"),
    ]
    flow_html = "".join(
        f'<div class="incident-step {tone}"><span class="step-number">{idx}</span>'
        f'<strong>{title}</strong><small>{detail}</small></div>'
        for idx, (title, detail, tone) in enumerate(steps, 1)
    )
    st.markdown(f'<div class="incident-flow">{flow_html}</div>', unsafe_allow_html=True)

    # Path comparison cards
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.markdown(f"""
        <div class="path-card">
            <small>① Original Baseline Route</small>
            <p>{escape(format_route(incident.get("previous_path")))}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_p2:
        st.markdown(f"""
        <div class="path-card blocked">
            <small>② Blocked Rogue Proposal (Rejected)</small>
            <p>{escape(format_route(incident.get("invalid_path")))}</p>
        </div>
        """, unsafe_allow_html=True)
    with col_p3:
        st.markdown(f"""
        <div class="path-card safe">
            <small>③ Recovered Safe Route (Dijkstra)</small>
            <p>{escape(format_route(safe_path))}</p>
        </div>
        """, unsafe_allow_html=True)

    # Violation details expander
    with st.expander("🔍 Security Audit — Why This Route Was Flagged and Rejected", expanded=True):
        st.markdown(f"**Target Destination:** Shared Database at Router H | **Penalized Trust Score:** `{client.trust_score} / 100`")
        for r in reasons:
            st.markdown(f"• <span style='color:#f87171;'>{escape(r)}</span>", unsafe_allow_html=True)
        if delivered:
            st.success("✓ Safe alternative route verified. Request successfully delivered to Database H without packet loss.", icon="🛡️")


def render_security_monitor(monitor: SecurityMonitor, viz_mode: str) -> None:
    """
    Renders the complete Security Testing workspace.
    Demonstrates: Malicious Client Simulation → Route Validation → Invalid Route Rejection → Safe Route Selection → Recovery
    """
    section_heading(
        "security-workspace",
        "02",
        "Security Testing — Simulate a Malicious Client",
        "Demonstrate detection of invalid routes, unauthorized hop rejection, and autonomous Dijkstra safe route recovery."
    )

    # Client Selection & Action Controls
    st.markdown('<div class="panel-title">🎮 Attack Simulation & Request Controls</div>', unsafe_allow_html=True)

    ctrl_col1, ctrl_col2, ctrl_col3, ctrl_col4 = st.columns([1.2, 1.2, 1.2, 1.2], gap="small")

    with ctrl_col1:
        selected = st.selectbox(
            "Select Client",
            list(monitor.clients),
            index=1,
            key="security_client",
            help="Choose which simulated client to inspect or test."
        )

    with ctrl_col2:
        st.write("")
        st.write("")
        attack_btn = st.button(
            "💥 Simulate Malicious Route",
            key="security_attack",
            use_container_width=True,
            help="Propose an unauthorized route through non-existent node 'Unauthorized X' and test automated validation and rejection."
        )

    with ctrl_col3:
        st.write("")
        st.write("")
        send_btn = st.button(
            "🚀 Send Database Request",
            key="security_send",
            type="primary",
            use_container_width=True,
            help="Send a legitimate database access request from the selected client."
        )

    with ctrl_col4:
        st.write("")
        st.write("")
        send_all_btn = st.button(
            "🌐 Send From All Clients",
            key="security_send_all",
            use_container_width=True,
            help="Simulate simultaneous database access requests from Client 1, Client 2, and Client 3."
        )

    # Action Handlers
    if attack_btn:
        monitor.simulate_attack(selected)
        st.rerun()

    if send_btn:
        monitor.request_database(selected)
        st.rerun()

    if send_all_btn:
        for client_id in monitor.clients:
            monitor.request_database(client_id)
        st.rerun()

    # Reset Security Simulation control
    res_c1, res_c2 = st.columns([3, 1])
    with res_c2:
        if st.button("🔄 Reset Security Simulation", key="security_reset", use_container_width=True,
                     help="Safely restores all 3 clients to pristine 100 Trust Score and NORMAL status."):
            for client in monitor.clients.values():
                client.status = "NORMAL"
                client.trust_score = 100
                client.blocked_requests = 0
                client.delivered = 0
                client.route_changes = 0
                client.last_request = "Not sent"
                client.last_incident = None
                monitor._recover(client, ["Security simulation reset"], initial=True)
            if monitor.event_sink:
                monitor.event_sink("[SECURITY] Security simulation reset to default baseline")
            st.rerun()

    # Client Telemetry Table (Requirement 4)
    st.markdown('<div class="panel-title">📊 Client Status & Measured Telemetry</div>', unsafe_allow_html=True)
    clients_telemetry_data = [
        calculate_client_telemetry(monitor, client)
        for client in monitor.clients.values()
    ]
    client_telemetry_table(clients_telemetry_data)

    # Terminology Help Expander
    terminology_guide()

    # Guided Incident Walkthrough (Requirement 5)
    selected_client = monitor.clients[selected]
    render_incident_walkthrough(selected_client)

    # Individual Client Trust Cards
    st.markdown('<div class="panel-title">👥 Client Reputation & Trust Cards</div>', unsafe_allow_html=True)
    card_cols = st.columns(3, gap="medium")
    for col, client in zip(card_cols, monitor.clients.values()):
        with col:
            render_client_card(client, client.client_id == selected)

    st.caption(
        "💡 Trust scores record incident history until network reset. "
        "A status of RECOVERED indicates the client's route is verified safe, preserving previous audit trails."
    )

    # Security Event Log Expander
    with st.expander("📜 Security Threat & Validation Audit Trail", expanded=False):
        st.caption("Latest security events, including intermediate detection, route rejection, and recovery logs.")
        if monitor.events:
            st.dataframe(list(reversed(monitor.events)), hide_index=True, use_container_width=True)
        else:
            st.info("No security events recorded yet.")
