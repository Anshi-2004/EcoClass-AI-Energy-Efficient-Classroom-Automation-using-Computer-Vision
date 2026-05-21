"""
AI Smart Classroom System - Streamlit Dashboard
=================================================
Ties together:
- YOLOv8 person detection  (detection.py)
- Smart AC control logic   (logic.py)
- Arduino serial control   (arduino.py)
- Real-time Streamlit dashboard with live video feed, logs, manual overrides
"""

import streamlit as st
import cv2
import numpy as np
import time
import csv
import io
from datetime import datetime
from detection import PersonDetector
from logic import ACController, AC_OFF, AC_LOW, AC_HIGH, AC_FULL_HIGH
from arduino import ArduinoController

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Smart Classroom System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Premium Dark CSS ──────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

html, body, [data-testid="stAppViewContainer"] {
    background: linear-gradient(135deg, #0f0c29 0%, #1a1a3e 40%, #24243e 100%) !important;
    color: #f0f0f5 !important;
    font-family: 'Inter', sans-serif !important;
}
[data-testid="stHeader"] {
    background: rgba(15,12,41,0.85) !important;
    backdrop-filter: blur(10px) !important;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg,#141432 0%,#1c1c4a 100%) !important;
    border-right: 1px solid rgba(139,92,246,0.25) !important;
}
[data-testid="stSidebar"] * { color:#e8e8f0 !important; }
[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 { color:#fff !important; font-weight:700 !important; }
[data-testid="stSidebar"] .stMarkdown p,
[data-testid="stSidebar"] .stMarkdown li,
[data-testid="stSidebar"] .stMarkdown span { color:#d0d0e0 !important; font-size:.95rem !important; opacity:1 !important; }
[data-testid="stSidebar"] hr { border-color:rgba(139,92,246,.3) !important; }

.main-title {
    font-size:2.2rem; font-weight:800;
    background:linear-gradient(90deg,#a78bfa,#60a5fa,#818cf8);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; text-align:center; padding:.8rem 0 .2rem; letter-spacing:-.02em;
}
.main-subtitle {
    text-align:center; color:#a0a0c0 !important; font-size:1.05rem; font-weight:400;
    margin-bottom:1.5rem; opacity:1 !important;
}

[data-testid="stMetric"] {
    background:linear-gradient(145deg,#1e1e50 0%,#252560 100%) !important;
    border:1px solid rgba(139,92,246,.3) !important; border-radius:16px !important;
    padding:1.2rem 1.4rem !important;
    box-shadow:0 8px 32px rgba(0,0,0,.35),0 0 20px rgba(139,92,246,.08) !important;
    transition:transform .2s ease,box-shadow .2s ease !important;
}
[data-testid="stMetric"]:hover {
    transform:translateY(-2px) !important;
    box-shadow:0 12px 40px rgba(0,0,0,.45),0 0 30px rgba(139,92,246,.15) !important;
}
[data-testid="stMetric"] label { color:#a0a0c8 !important; font-weight:600 !important; font-size:.85rem !important; text-transform:uppercase !important; letter-spacing:.08em !important; opacity:1 !important; }
[data-testid="stMetric"] [data-testid="stMetricValue"] { color:#fff !important; font-weight:800 !important; font-size:1.9rem !important; }
[data-testid="stMetric"] [data-testid="stMetricDelta"] { color:#8b5cf6 !important; font-weight:600 !important; opacity:1 !important; }

.stAlert > div {
    background:rgba(30,30,80,.7) !important; border:1px solid rgba(139,92,246,.3) !important;
    border-radius:12px !important; color:#e8e8f0 !important; padding:1rem !important;
}
.stAlert > div p { color:#e8e8f0 !important; opacity:1 !important; }

.stButton > button {
    background:linear-gradient(135deg,#7c3aed 0%,#6d28d9 50%,#5b21b6 100%) !important;
    color:#fff !important; border:none !important; border-radius:12px !important;
    padding:.7rem 2rem !important; font-weight:700 !important; font-size:1rem !important;
    letter-spacing:.03em !important; box-shadow:0 4px 20px rgba(124,58,237,.35) !important;
    transition:all .3s ease !important; width:100% !important;
}
.stButton > button:hover {
    background:linear-gradient(135deg,#8b5cf6 0%,#7c3aed 50%,#6d28d9 100%) !important;
    box-shadow:0 6px 28px rgba(139,92,246,.5) !important; transform:translateY(-1px) !important;
}
.stButton > button:active { transform:translateY(0) !important; }

.live-feed-header { color:#fff !important; font-size:1.1rem !important; font-weight:700 !important; margin-bottom:.5rem !important; display:flex !important; align-items:center !important; gap:.5rem !important; }
.live-dot { width:10px; height:10px; background:#ef4444; border-radius:50%; display:inline-block; animation:pulse-dot 1.5s infinite; }
@keyframes pulse-dot { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(239,68,68,.7)} 50%{opacity:.8;box-shadow:0 0 0 6px rgba(239,68,68,0)} }

[data-testid="stImage"] { border-radius:12px !important; overflow:hidden !important; }
[data-testid="stImage"] img { border-radius:12px !important; }

.status-card {
    background:linear-gradient(145deg,#1e1e50 0%,#252560 100%) !important;
    border:1px solid rgba(139,92,246,.3) !important; border-radius:14px !important;
    padding:1.1rem 1.4rem !important; box-shadow:0 6px 24px rgba(0,0,0,.25) !important;
    color:#e8e8f0 !important; font-size:1rem !important; font-weight:500 !important; margin:.5rem 0 !important;
}
.alert-high {
    background:linear-gradient(145deg,#7f1d1d 0%,#991b1b 100%) !important;
    border:1px solid rgba(239,68,68,.6) !important; border-radius:14px !important;
    padding:1rem 1.4rem !important; color:#fecaca !important; font-weight:700 !important;
    font-size:1.05rem !important; margin:.5rem 0 !important; text-align:center;
    animation:pulse-alert 1.5s infinite;
}
@keyframes pulse-alert { 0%,100%{box-shadow:0 0 0 0 rgba(239,68,68,.5)} 50%{box-shadow:0 0 0 8px rgba(239,68,68,0)} }

.ac-badge {
    display:inline-block; padding:.3rem .9rem; border-radius:30px; font-weight:700;
    font-size:.95rem; margin:.2rem;
}
.badge-off  { background:#374151; color:#9ca3af; }
.badge-low  { background:#065f46; color:#6ee7b7; }
.badge-high { background:#1e3a5f; color:#60a5fa; }
.badge-full { background:#4c1d95; color:#c4b5fd; }

.log-box {
    background:#0f0f2e !important; border:1px solid rgba(139,92,246,.2) !important;
    border-radius:12px !important; padding:.8rem 1rem !important;
    font-family:'Courier New',monospace !important; font-size:.78rem !important;
    color:#a0a0d0 !important; max-height:180px; overflow-y:auto;
}

hr { border-color:rgba(139,92,246,.2) !important; }
.stMarkdown,.stMarkdown p,.stMarkdown span,.stMarkdown li,
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3,.stMarkdown h4,
.stMarkdown h5,.stMarkdown h6,.stText,label,.stCaption p { color:#e8e8f0 !important; opacity:1 !important; }
.stMarkdown h1,.stMarkdown h2,.stMarkdown h3 { color:#fff !important; font-weight:700 !important; }
.stCaption,.stCaption p { color:#b0b0d0 !important; opacity:1 !important; }
[data-testid="stSelectbox"] label,[data-testid="stSlider"] label,
[data-testid="stNumberInput"] label,[data-testid="stTextInput"] label { color:#d0d0e8 !important; font-weight:600 !important; opacity:1 !important; }
[data-testid="stSelectbox"] > div > div,.stSelectbox > div > div { background:#1e1e50 !important; border-color:rgba(139,92,246,.3) !important; color:#e8e8f0 !important; }
.stProgress > div > div { background:linear-gradient(90deg,#7c3aed,#60a5fa) !important; border-radius:10px !important; }
.stProgress > div { background:rgba(30,30,80,.5) !important; border-radius:10px !important; }
::-webkit-scrollbar { width:8px; }
::-webkit-scrollbar-track { background:#1a1a3e; }
::-webkit-scrollbar-thumb { background:#4a4a8a; border-radius:4px; }
::-webkit-scrollbar-thumb:hover { background:#6a6aaa; }
[data-testid="column"] { padding:0 .5rem !important; }
.stTabs [data-baseweb="tab-list"] { gap:.5rem !important; }
.stTabs [data-baseweb="tab"] { background:rgba(30,30,80,.5) !important; color:#b0b0d0 !important; border-radius:10px 10px 0 0 !important; padding:.5rem 1.2rem !important; font-weight:600 !important; }
.stTabs [aria-selected="true"] { background:rgba(139,92,246,.3) !important; color:#fff !important; }
</style>
""", unsafe_allow_html=True)


# ── AC level display helpers ──────────────────────────────────────────────────
BADGE_CLASS = {
    AC_OFF:       "badge-off",
    AC_LOW:       "badge-low",
    AC_HIGH:      "badge-high",
    AC_FULL_HIGH: "badge-full",
}
LEVEL_LABELS = {AC_OFF: "OFF", AC_LOW: "LOW", AC_HIGH: "HIGH", AC_FULL_HIGH: "FULL HIGH"}


def ac_badge(level: int) -> str:
    cls = BADGE_CLASS.get(level, "badge-off")
    lbl = LEVEL_LABELS.get(level, "OFF")
    return f'<span class="ac-badge {cls}">⚡ AC {lbl}</span>'


# ── Session-state initialisation ─────────────────────────────────────────────
def _init_state():
    defaults = {
        "running":    False,
        "detector":   PersonDetector(),
        "controller": ACController(),
        "frame_count": 0,
        "fps":        0.0,
        "dl_counter": 0,   # increments each update to give download_button a unique key
        "logs":       [],          # list of log-entry dicts
        "arduino":    None,        # ArduinoController instance (created on demand)
        "com_port":   "AUTO",
        "last_state": {
            "ac_on": False, "ac_level": 0, "ac_label": "OFF",
            "temperature": None, "room_status": "Empty",
            "message": "System ready — press Start to begin.",
            "energy_saving_pct": 100.0, "person_count": 0, "empty_countdown": None,
        },
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

_init_state()


# ── Logging helper ────────────────────────────────────────────────────────────
def add_log(msg: str, kind: str = "info"):
    ts = datetime.now().strftime("%H:%M:%S")
    st.session_state.logs.append({"time": ts, "msg": msg, "kind": kind})
    if len(st.session_state.logs) > 200:
        st.session_state.logs.pop(0)


# ── Arduino helper ────────────────────────────────────────────────────────────
def get_arduino() -> ArduinoController:
    """Return (creating if needed) the ArduinoController."""
    if st.session_state.arduino is None:
        port = st.session_state.com_port
        st.session_state.arduino = ArduinoController(port=port)
        add_log(f"Arduino controller started (port={port})", "info")
    return st.session_state.arduino


def send_to_arduino(level: int):
    try:
        ard = get_arduino()
        ok = ard.send_level(level)
        if not ok and ard.is_connected is False:
            add_log("Arduino not connected — retrying...", "warn")
    except Exception as exc:
        add_log(f"Arduino error: {exc}", "error")


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎛️ Control Panel")
    st.markdown("---")

    col_start, col_stop = st.columns(2)
    with col_start:
        if st.button("▶ Start", key="start_btn", use_container_width=True):
            st.session_state.running = True
            add_log("Detection started", "info")
    with col_stop:
        if st.button("⏹ Stop", key="stop_btn", use_container_width=True):
            st.session_state.running = False
            add_log("Detection stopped", "info")

    st.markdown("---")

    # ── Arduino COM port ──────────────────────────────────────────────────
    st.markdown("### 🔌 Arduino Connection")
    available_ports = ArduinoController.list_ports()
    port_options = ["AUTO", "NONE"] + available_ports
    selected_port = st.selectbox(
        "COM Port", port_options,
        index=port_options.index(st.session_state.com_port)
              if st.session_state.com_port in port_options else 0,
        key="com_selector",
    )

    if selected_port != st.session_state.com_port:
        st.session_state.com_port = selected_port
        if st.session_state.arduino is not None:
            st.session_state.arduino.reconnect(
                None if selected_port == "AUTO" else selected_port
            )
            add_log(f"COM port changed to {selected_port}", "info")


    col_r, col_d = st.columns(2)
    with col_r:
        if st.button("🔄 Reconnect", key="reconnect_btn", use_container_width=True):
            if st.session_state.arduino is not None:
                ok = st.session_state.arduino.reconnect(
                    None if selected_port in ("AUTO", "NONE") else selected_port
                )
                add_log(
                    "Arduino reconnected ✔" if ok else "Reconnect failed — check cable/port",
                    "info" if ok else "error",
                )
            else:
                get_arduino()
    with col_d:
        if st.button("🔓 Release Port", key="release_btn", use_container_width=True):
            if st.session_state.arduino is not None:
                st.session_state.arduino.disconnect()
                st.session_state.arduino = None
                add_log("COM port released — safe to upload Arduino sketch", "info")

    ard_status = "🔴 Not Connected"
    if st.session_state.arduino and st.session_state.arduino.is_connected:
        ard_status = f"🟢 {st.session_state.arduino.active_port}"
    st.markdown(f"**Status:** `{ard_status}`")
    if st.session_state.arduino is None:
        st.info("ℹ️ Port released. Upload your sketch, then click Reconnect.")

    st.markdown("---")

    # ── Manual AC override buttons ────────────────────────────────────────
    st.markdown("### ⚙️ Manual AC Override")
    manual_levels = {
        "🔴 OFF":       AC_OFF,
        "🟡 LOW":       AC_LOW,
        "🔵 HIGH":      AC_HIGH,
        "🟣 FULL HIGH": AC_FULL_HIGH,
    }
    for btn_label, lvl in manual_levels.items():
        if st.button(btn_label, key=f"manual_{lvl}"):
            new_state = st.session_state.controller.force_level(lvl)
            st.session_state.last_state = new_state
            send_to_arduino(lvl)
            add_log(f"Manual override → AC {LEVEL_LABELS[lvl]}", "override")

    st.markdown("---")
    st.markdown("### ℹ️ System Info")
    st.markdown(f"""
- **Model:** YOLOv8n (Nano)
- **Confidence:** 45 %
- **Empty Delay:** 30 s
- **Status:** {"🟢 Running" if st.session_state.running else "🔴 Stopped"}
    """)
    st.markdown("---")
    st.markdown("### 📖 How It Works")
    st.markdown("""
1. Camera detects students via YOLOv8
2. Count → AC level (OFF/LOW/HIGH/FULL)
3. Command sent to Arduino over serial
4. Arduino lights LEDs (D8/D9/D10)
5. AC level badge shown on dashboard
    """)
    st.markdown("---")
    st.markdown(
        "<p style='text-align:center;color:#8080b0!important;font-size:.8rem;opacity:1!important'>"
        "Built with Streamlit + YOLOv8 + Arduino</p>",
        unsafe_allow_html=True,
    )


# ── Main title ────────────────────────────────────────────────────────────────
st.markdown('<div class="main-title">AI Smart Classroom System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="main-subtitle">Intelligent Occupancy Detection &amp; Energy-Efficient AC Control via Arduino</div>',
    unsafe_allow_html=True,
)

# ── Metric placeholders ───────────────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)
with col1: metric_people   = st.empty()
with col2: metric_room     = st.empty()
with col3: metric_ac       = st.empty()
with col4: metric_temp     = st.empty()
with col5: metric_energy   = st.empty()

st.markdown("")
alert_placeholder  = st.empty()
status_msg_placeholder = st.empty()
st.markdown("")

# ── Main columns: feed + info ────────────────────────────────────────────────
feed_col, info_col = st.columns([3, 1])

with feed_col:
    st.markdown(
        '<div class="live-feed-header"><span class="live-dot"></span> Live Camera Feed</div>',
        unsafe_allow_html=True,
    )
    frame_placeholder = st.empty()

with info_col:
    st.markdown("### Detection Details")
    details_placeholder  = st.empty()
    countdown_placeholder = st.empty()
    st.markdown("#### Energy Efficiency")
    energy_bar_placeholder = st.empty()
    st.markdown("#### AC Level")
    ac_badge_placeholder = st.empty()

st.markdown("---")

# ── Tabs: Logs ────────────────────────────────────────────────────────────────
tab_logs, tab_export = st.tabs(["📋 Activity Log", "📥 Export Logs"])

with tab_logs:
    logs_placeholder = st.empty()

with tab_export:
    st.markdown("Download the full activity log as a CSV file.")
    export_btn = st.empty()


# ── Dashboard update function ─────────────────────────────────────────────────
def update_dashboard(state: dict, fps: float):
    level = state.get("ac_level", AC_OFF)

    metric_people.metric("People Detected",  state["person_count"])
    metric_room.metric("Room Status",         state["room_status"])
    metric_ac.metric("AC Status",             "ON" if state["ac_on"] else "OFF")
    temp_disp = f'{state["temperature"]}°C' if state["temperature"] else "-- °C"
    metric_temp.metric("Temperature",         temp_disp)
    metric_energy.metric("Energy Saving",     f'{state["energy_saving_pct"]}%')

    # High-occupancy alert
    if state["person_count"] > 25:
        alert_placeholder.markdown(
            '<div class="alert-high">🚨 HIGH OCCUPANCY ALERT — More than 25 students detected!</div>',
            unsafe_allow_html=True,
        )
    else:
        alert_placeholder.empty()

    status_msg_placeholder.markdown(
        f'<div class="status-card">{state["message"]}</div>',
        unsafe_allow_html=True,
    )

    temp_val = state["temperature"] if state["temperature"] else "--"
    details_placeholder.markdown(
        f'<div class="status-card">'
        f'Persons: {state["person_count"]}<br>'
        f'Temp: {temp_val}°C<br>'
        f'Energy Save: {state["energy_saving_pct"]}%<br>'
        f'FPS: {fps:.1f}'
        f'</div>',
        unsafe_allow_html=True,
    )

    if state["empty_countdown"] is not None and state["empty_countdown"] > 0:
        countdown_placeholder.markdown(
            f'<div class="status-card">⏳ AC off in {state["empty_countdown"]}s</div>',
            unsafe_allow_html=True,
        )
    else:
        countdown_placeholder.empty()

    energy_bar_placeholder.progress(int(state["energy_saving_pct"]) / 100)
    ac_badge_placeholder.markdown(ac_badge(level), unsafe_allow_html=True)

    # Render logs
    log_html = '<div class="log-box">'
    for entry in reversed(st.session_state.logs[-50:]):
        colour = {"info": "#a0a0d0", "warn": "#fbbf24", "error": "#f87171", "override": "#818cf8"}.get(entry["kind"], "#a0a0d0")
        log_html += f'<span style="color:{colour}">[{entry["time"]}] {entry["msg"]}</span><br>'
    log_html += "</div>"
    logs_placeholder.markdown(log_html, unsafe_allow_html=True)

    # Export button
    if st.session_state.logs:
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["time", "kind", "msg"])
        writer.writeheader()
        writer.writerows(st.session_state.logs)
        st.session_state.dl_counter += 1
        export_btn.download_button(
            "⬇️ Download CSV", buf.getvalue(),
            file_name="classroom_log.csv", mime="text/csv",
            key=f"dl_csv_{st.session_state.dl_counter}",
        )


# ── Show idle state ───────────────────────────────────────────────────────────
if not st.session_state.running:
    update_dashboard(st.session_state.last_state, st.session_state.fps)
    placeholder_img = np.zeros((480, 640, 3), dtype=np.uint8)
    placeholder_img[:] = (20, 20, 50)
    cv2.putText(placeholder_img, "Camera Paused",              (180, 230),
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, (160, 140, 200), 2, cv2.LINE_AA)
    cv2.putText(placeholder_img, "Press START to begin detection", (120, 280),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (120, 110, 170), 1, cv2.LINE_AA)
    frame_placeholder.image(placeholder_img, channels="BGR", use_column_width=True)


# ── Real-time detection loop ──────────────────────────────────────────────────
if st.session_state.running:
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        st.error("Could not open webcam. Please check your camera connection.")
        st.session_state.running = False
        add_log("Camera open failed", "error")
    else:
        add_log("Camera opened successfully", "info")
        prev_level = -1
        warmup_until = time.time() + 3.0   # ignore first 3 s (camera warmup)

        # ── Force Arduino to OFF on every fresh start ──────────────
        send_to_arduino(AC_OFF)
        st.session_state.controller.force_level(AC_OFF)
        add_log("Arduino reset to OFF on start", "info")

        try:
            while st.session_state.running:
                loop_start = time.time()

                ret, frame = cap.read()
                if not ret:
                    time.sleep(0.5)
                    add_log("Frame read failed — retrying", "warn")
                    continue

                # ── YOLOv8 detection ──────────────────────────────────
                annotated_frame, person_count, boxes = (
                    st.session_state.detector.detect(frame)
                )

                # ── AC controller ─────────────────────────────────────
                # During camera warmup: treat count as 0 to avoid YOLO
                # false-positives from camera initialization
                effective_count = 0 if time.time() < warmup_until else person_count
                new_state = st.session_state.controller.update(effective_count)
                st.session_state.last_state = new_state

                # ── Send to Arduino only on level change ──────────────
                current_level = new_state["ac_level"]
                if current_level != prev_level:
                    send_to_arduino(current_level)
                    add_log(
                        f"AC → {LEVEL_LABELS[current_level]} "
                        f"(students: {effective_count})",
                        "info",
                    )
                    prev_level = current_level

                # ── FPS ───────────────────────────────────────────────
                elapsed = time.time() - loop_start
                st.session_state.fps = 1.0 / max(elapsed, 0.001)
                st.session_state.frame_count += 1

                # ── Update live feed ──────────────────────────────────
                rgb_frame = cv2.cvtColor(annotated_frame, cv2.COLOR_BGR2RGB)
                frame_placeholder.image(rgb_frame, channels="RGB", use_column_width=True)

                # ── Update all metrics ────────────────────────────────
                update_dashboard(new_state, st.session_state.fps)

                time.sleep(0.05)

        except Exception as exc:
            st.error(f"Detection error: {exc}")
            add_log(f"Exception: {exc}", "error")
        finally:
            # ── Always turn LEDs OFF when camera stops ──────────────
            send_to_arduino(AC_OFF)
            st.session_state.controller.force_level(AC_OFF)
            add_log("Arduino reset to OFF on stop", "info")
            cap.release()
            add_log("Camera released", "info")
