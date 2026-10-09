"""
ui/components.py - Reusable presentation components for MeshGuard NOC Dashboard.
"""

from html import escape
from pathlib import Path
from typing import List, Dict, Any, Optional

import streamlit as st


def load_styles() -> None:
    """Loads the Cyber NOC custom CSS design system."""
    css_path = Path(__file__).with_name("styles.css")
    if css_path.exists():
        css = css_path.read_text(encoding="utf-8")
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


def section_heading(anchor: str, number: str, title: str, description: str) -> None:
    """Renders a structured section header with anchor link and eyebrow."""
    st.markdown(
        f'<section id="{escape(anchor)}" class="section-heading">'
        f'<div class="eyebrow">{escape(number)} / WORKSPACE</div>'
        f'<h2>{escape(title)}</h2><p>{escape(description)}</p></section>',
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: str, detail: str, tone: str = "cyan") -> None:
    """Renders a high-tech telemetry metric card."""
    st.markdown(
        f'<div class="metric-card tone-{tone}">'
        f'<div class="metric-label">{escape(label)}</div>'
        f'<div class="metric-value">{escape(value)}</div>'
        f'<div class="metric-detail"><span class="metric-dot"></span>{escape(detail)}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def workflow_stepper(current_step: str, status_message: str, is_blocked: bool = False) -> None:
    """
    Renders the autonomous self-healing and security workflow panel:
    Monitor → Detect → Validate → Block → Reroute → Recover
    """
    steps = ["Monitor", "Detect", "Validate", "Block", "Reroute", "Recover"]
    step_indices = {s.upper(): idx for idx, s in enumerate(steps)}

    cur_upper = current_step.upper()
    cur_idx = step_indices.get(cur_upper, 0)

    step_html_items = []
    for idx, s in enumerate(steps):
        s_upper = s.upper()
        if is_blocked and s_upper == "BLOCK":
            cls = "step-blocked step-active"
        elif idx == cur_idx:
            cls = "step-active"
        elif idx < cur_idx:
            cls = "step-completed"
        else:
            cls = "step-idle"

        step_html_items.append(
            f'<div class="workflow-step {cls}">'
            f'<div class="step-idx">0{idx + 1}</div>'
            f'<div class="step-title">{s}</div>'
            f'</div>'
        )

    track_html = "".join(step_html_items)

    st.markdown(
        f'<div class="workflow-panel">'
        f'<div class="workflow-header">'
        f'<span class="eyebrow">AUTOMATED NETWORK WORKFLOW PIPELINE</span>'
        f'<span style="font-size:11px; color:#889bb4; font-family:Consolas,monospace;">STATE: {escape(current_step.upper())}</span>'
        f'</div>'
        f'<div class="workflow-track">{track_html}</div>'
        f'<div class="workflow-status-bar">'
        f'<span class="status-tag">TELEMETRY</span>'
        f'<span>{escape(status_message)}</span>'
        f'</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def client_telemetry_table(clients_data: List[Dict[str, Any]]) -> None:
    """
    Renders an easy-to-read client status and telemetry table:
    Client | Current Path | Measured RTT | Drift | Status | Security Classification | Trust Score
    """
    rows_html = []
    for c in clients_data:
        client_name = escape(c.get("name", "Client"))
        path_str = escape(c.get("path", "No safe route"))

        rtt_str = escape(str(c.get("rtt", "N/A")))
        drift_str = escape(str(c.get("drift", "+0.0 ms")))

        status = c.get("status", "Online")
        status_pill_cls = "badge-normal" if status == "Online" else "badge-malicious" if status == "Isolated" else "badge-suspicious"

        security = c.get("security", "NORMAL")
        sec_pill_cls = (
            "badge-normal" if security == "NORMAL"
            else "badge-recovered" if security == "RECOVERED"
            else "badge-suspicious" if security == "SUSPICIOUS"
            else "badge-malicious"
        )

        trust = c.get("trust_score", 100)
        trust_color = "#10b981" if trust >= 80 else "#f59e0b" if trust >= 50 else "#f43f5e"

        rows_html.append(
            f'<tr>'
            f'<td><strong>{client_name}</strong></td>'
            f'<td><code style="color:#7dd3fc; background:transparent; font-size:11.5px;">{path_str}</code></td>'
            f'<td><strong>{rtt_str}</strong></td>'
            f'<td><span style="color:#94a3b8; font-family:Consolas,monospace;">{drift_str}</span></td>'
            f'<td><span class="badge-tag {status_pill_cls}">{escape(status)}</span></td>'
            f'<td><span class="badge-tag {sec_pill_cls}">{escape(security)}</span></td>'
            f'<td>'
            f'<div style="display:flex; align-items:center; gap:8px;">'
            f'<div style="flex:1; height:4px; background:#1e2c40; border-radius:3px; overflow:hidden;">'
            f'<div style="width:{trust}%; height:100%; background:{trust_color};"></div>'
            f'</div>'
            f'<span style="font-family:Consolas,monospace; font-size:11px; font-weight:700;">{trust}</span>'
            f'</div>'
            f'</td>'
            f'</tr>'
        )

    tbody = "".join(rows_html)

    st.markdown(
        f'<div class="table-container">'
        f'<table class="custom-table">'
        f'<thead>'
        f'<tr>'
        f'<th>Client</th>'
        f'<th>Current Communication Path</th>'
        f'<th>Dijkstra Metric Cost</th>'
        f'<th>Hop Count</th>'
        f'<th>Node Status</th>'
        f'<th>Security Classification</th>'
        f'<th>Trust Score</th>'
        f'</tr>'
        f'</thead>'
        f'<tbody>{tbody}</tbody>'
        f'</table>'
        f'</div>',
        unsafe_allow_html=True,
    )


def terminology_guide() -> None:
    """Renders expandable help section with honest technical definitions."""
    with st.expander("📘 Technical Metrics & Networking Terms Guide", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("""
            * **Dijkstra's Algorithm:** Calculates the lowest total metric weight path across the operational network subgraph.
            * **Route Cost (Metric Weight):** The cumulative sum of link weights along the computed path (representing administrative link cost/bandwidth).
            * **Hop Count:** Number of router-to-router forwarding steps (path node count minus 1).
            """)
        with c2:
            st.markdown("""
            * **Autonomous Self-Healing:** Capability to automatically detect link severances or hardware crashes, recompute alternate loop-free shortest paths via Dijkstra, and restore connectivity in milliseconds.
            * **Trust Score:** Dynamic reputation metric (0–100). Valid requests maintain high trust; rogue or disconnected route proposals incur penalties.
            * **Simulated Recovery Time:** Wall-clock duration in seconds measured during failure detection and Dijkstra recalculation.
            """)


def viva_demo_guide() -> None:
    """Renders a step-by-step viva presentation guide for demonstration."""
    with st.expander("📋 9-Step Project Demonstration & Viva Walkthrough Guide", expanded=False):
        st.markdown("""
        Use this structured sequence during laboratory evaluations and viva presentations:
        """)
        st.markdown("""
        <div class="demo-step-list">
            <div class="demo-step-card">
                <span class="step-num">STEP 01</span>
                <strong>Start with 3 Normal Clients</strong>
                <span>Observe initial topology: all 3 clients connect to Router A and route through healthy routers to Database H.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 02</span>
                <strong>Show Baseline Routes</strong>
                <span>Check client table and metrics: optimal path <code>A → B → D → F → H</code> with lowest Dijkstra metric cost (10).</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 03</span>
                <strong>Trigger Link Failure</strong>
                <span>Go to <em>Network Failure Testing</em>, select Link <code>D - F</code>, and click <strong>Sever Link</strong>.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 04</span>
                <strong>Observe Self-Healing</strong>
                <span>Watch autonomous reroute banner: failure detected in milliseconds, Dijkstra switches path to <code>A → B → D → H</code>.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 05</span>
                <strong>Restore Network</strong>
                <span>Use <strong>Restore Selected Link</strong> or <strong>Reset Entire Network</strong> to return to pristine baseline.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 06</span>
                <strong>Simulate Malicious Client</strong>
                <span>Switch to <em>Security Testing</em> tab, select <strong>Client 2</strong>, and click <strong>Simulate Malicious Route</strong>.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 07</span>
                <strong>Show Invalid Route Rejection</strong>
                <span>Notice the security alert: rogue path via <code>Unauthorized X</code> is rejected and blocked. Zero packets forwarded.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 08</span>
                <strong>Safe Route Recovery</strong>
                <span>Dijkstra recalculates a verified safe route on authorized nodes. Client 2 recovers safely.</span>
            </div>
            <div class="demo-step-card">
                <span class="step-num">STEP 09</span>
                <strong>Verify Other Clients Unaffected</strong>
                <span>Verify Client 1 and Client 3 remain at 100 Trust Score with normal operational status throughout the incident.</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
