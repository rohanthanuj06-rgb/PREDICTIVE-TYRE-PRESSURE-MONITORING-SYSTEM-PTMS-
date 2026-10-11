"""
Predictive Tyre Monitoring System (PTMS) - Sensor Data & Live Graphs Page
High-performance real-time telemetry waveforms via PyQtGraph:
- Pressure vs Time (with nominal & hazard thresholds)
- Temperature vs Time (with thermal boundaries)
- Predictive Risk Score vs Time (0-100%)
"""

from collections import deque
import pyqtgraph as pg
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QComboBox, QPushButton, QButtonGroup, QRadioButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)

# Configure PyQtGraph global options for modern automotive dark UI
pg.setConfigOption("background", "#0d1117")
pg.setConfigOption("foreground", "#8b949e")
pg.setConfigOption("antialias", True)


class SensorDataView(QWidget):
    """
    Live real-time telemetry graphs view.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.buffer_len = 120  # ~2 minutes of data at 1Hz decimation
        self.selected_tyre = "ALL"  # "ALL", "FL", "FR", "RL", "RR"
        self.is_paused = False

        # Data circular buffers
        self.time_buffer = deque(maxlen=self.buffer_len)
        self.start_sim_time = None

        self.tyre_buffers = {
            "FL": {"p": deque(maxlen=self.buffer_len), "t": deque(maxlen=self.buffer_len), "r": deque(maxlen=self.buffer_len)},
            "FR": {"p": deque(maxlen=self.buffer_len), "t": deque(maxlen=self.buffer_len), "r": deque(maxlen=self.buffer_len)},
            "RL": {"p": deque(maxlen=self.buffer_len), "t": deque(maxlen=self.buffer_len), "r": deque(maxlen=self.buffer_len)},
            "RR": {"p": deque(maxlen=self.buffer_len), "t": deque(maxlen=self.buffer_len), "r": deque(maxlen=self.buffer_len)},
        }

        # Color schemes for tyres
        self.tyre_colors = {
            "FL": "#58a6ff",  # Bright Cyan
            "FR": "#7ee787",  # Soft Green
            "RL": "#f0883e",  # Orange / Amber (Primary fault focus)
            "RR": "#bc8cff"   # Violet
        }

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(12)

        # Top Control Bar
        top_bar = QHBoxLayout()
        title_box = QVBoxLayout()
        lbl_title = QLabel("LIVE SENSOR TELEMETRY & WAVEFORM OSCILLOSCOPE")
        lbl_title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {COLOR_CYAN};")
        lbl_sub = QLabel("Continuous 10 Hz telemetry streaming: Pressure (PSI), Temperature (°C), and Risk Index (%)")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        top_bar.addLayout(title_box)
        top_bar.addStretch()

        # Tyre Filter Radio Buttons
        self.btn_group = QButtonGroup(self)
        for label in ("ALL", "RL", "FL", "FR", "RR"):
            rb = QRadioButton(label)
            rb.setStyleSheet(f"color: {TEXT_PRIMARY}; font-weight: 600; padding: 4px 8px;")
            if label == "ALL":
                rb.setChecked(True)
            self.btn_group.addButton(rb)
            top_bar.addWidget(rb)
            rb.toggled.connect(lambda checked, l=label: self._on_filter_changed(l, checked))

        self.btn_pause = QPushButton("⏸ Pause")
        self.btn_pause.setProperty("class", "SecondaryBtn")
        self.btn_pause.clicked.connect(self._toggle_pause)
        top_bar.addWidget(self.btn_pause)

        main_layout.addLayout(top_bar)

        # Graph Container Frame
        graph_frame = QFrame()
        graph_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 10px;
            }}
        """)
        g_layout = QVBoxLayout(graph_frame)
        g_layout.setSpacing(8)

        # 1. Pressure Plot Widget
        self.plot_pressure = pg.PlotWidget(title="<b>TYRE PRESSURE vs TIME (PSI)</b>")
        self.plot_pressure.showGrid(x=True, y=True, alpha=0.2)
        self.plot_pressure.setLabel("left", "Pressure", units="PSI")
        self.plot_pressure.setLabel("bottom", "Time (seconds)")
        self.plot_pressure.setYRange(15, 45)
        # Add safety threshold lines
        self.plot_pressure.addLine(y=32.0, pen=pg.mkPen("#2ea043", width=1.5, style=Qt.DashLine))
        self.plot_pressure.addLine(y=26.0, pen=pg.mkPen("#d29922", width=1.2, style=Qt.DashLine))
        self.plot_pressure.addLine(y=22.0, pen=pg.mkPen("#f85149", width=1.5, style=Qt.DashLine))
        g_layout.addWidget(self.plot_pressure)

        # 2. Temperature Plot Widget
        self.plot_temp = pg.PlotWidget(title="<b>TYRE TEMPERATURE vs TIME (°C)</b>")
        self.plot_temp.showGrid(x=True, y=True, alpha=0.2)
        self.plot_temp.setLabel("left", "Temperature", units="°C")
        self.plot_temp.setLabel("bottom", "Time (seconds)")
        self.plot_temp.setYRange(20, 90)
        self.plot_temp.addLine(y=60.0, pen=pg.mkPen("#d29922", width=1.2, style=Qt.DashLine))
        self.plot_temp.addLine(y=75.0, pen=pg.mkPen("#f85149", width=1.5, style=Qt.DashLine))
        g_layout.addWidget(self.plot_temp)

        # 3. Risk Score Plot Widget
        self.plot_risk = pg.PlotWidget(title="<b>PREDICTIVE RISK SCORE vs TIME (%)</b>")
        self.plot_risk.showGrid(x=True, y=True, alpha=0.2)
        self.plot_risk.setLabel("left", "Risk", units="%")
        self.plot_risk.setLabel("bottom", "Time (seconds)")
        self.plot_risk.setYRange(0, 100)
        self.plot_risk.addLine(y=40.0, pen=pg.mkPen("#3fb950", width=1.0, style=Qt.DashLine))
        self.plot_risk.addLine(y=60.0, pen=pg.mkPen("#d29922", width=1.2, style=Qt.DashLine))
        self.plot_risk.addLine(y=80.0, pen=pg.mkPen("#f85149", width=1.5, style=Qt.DashLine))
        g_layout.addWidget(self.plot_risk)

        main_layout.addWidget(graph_frame, 1)

        # Initialize Plot Curves
        self.curves_p = {}
        self.curves_t = {}
        self.curves_r = {}

        for tid in ("FL", "FR", "RL", "RR"):
            c = self.tyre_colors[tid]
            self.curves_p[tid] = self.plot_pressure.plot(pen=pg.mkPen(c, width=2.2), name=tid)
            self.curves_t[tid] = self.plot_temp.plot(pen=pg.mkPen(c, width=2.2), name=tid)
            self.curves_r[tid] = self.plot_risk.plot(pen=pg.mkPen(c, width=2.2), name=tid)

    def _on_filter_changed(self, label: str, checked: bool):
        if checked:
            self.selected_tyre = label
            self._update_curve_visibility()

    def _update_curve_visibility(self):
        for tid in ("FL", "FR", "RL", "RR"):
            vis = (self.selected_tyre == "ALL" or self.selected_tyre == tid)
            self.curves_p[tid].setVisible(vis)
            self.curves_t[tid].setVisible(vis)
            self.curves_r[tid].setVisible(vis)

    def _toggle_pause(self):
        self.is_paused = not self.is_paused
        self.btn_pause.setText("▶ Resume" if self.is_paused else "⏸ Pause")

    def update_state(self, snapshot: dict):
        if self.is_paused:
            return

        ts = snapshot.get("timestamp")
        if self.start_sim_time is None:
            self.start_sim_time = ts

        rel_time = ts - self.start_sim_time
        self.time_buffer.append(rel_time)

        tyres = snapshot.get("tyres", {})
        for tid in ("FL", "FR", "RL", "RR"):
            d = tyres.get(tid, {})
            p = d.get("pressure_psi", 32.0)
            t = d.get("temperature_c", 33.0)
            r = d.get("risk_score", 10.0)

            self.tyre_buffers[tid]["p"].append(p)
            self.tyre_buffers[tid]["t"].append(t)
            self.tyre_buffers[tid]["r"].append(r)

        # Update curve datasets
        t_arr = list(self.time_buffer)
        for tid in ("FL", "FR", "RL", "RR"):
            self.curves_p[tid].setData(t_arr, list(self.tyre_buffers[tid]["p"]))
            self.curves_t[tid].setData(t_arr, list(self.tyre_buffers[tid]["t"]))
            self.curves_r[tid].setData(t_arr, list(self.tyre_buffers[tid]["r"]))
