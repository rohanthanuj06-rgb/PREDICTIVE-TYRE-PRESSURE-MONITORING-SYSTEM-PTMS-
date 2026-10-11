"""
Predictive Tyre Monitoring System (PTMS) - Dashboard View
Main Automotive Control & Status Overview.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QPushButton, QProgressBar, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    get_status_color, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class TyreStatusCard(QFrame):
    """
    Card displaying real-time metrics for a single tyre (FL, FR, RL, RR).
    """

    def __init__(self, tyre_id: str, title: str, parent=None):
        super().__init__(parent)
        self.tyre_id = tyre_id
        self.setObjectName(f"card_{tyre_id}")
        self.setStyleSheet(f"""
            QFrame#card_{tyre_id} {{
                background-color: {BG_CARD};
                border: 2px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 12px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # Header: Tyre Name & Status Badge
        header_layout = QHBoxLayout()
        self.lbl_title = QLabel(f"<b>{tyre_id}</b> <span style='color:{TEXT_MUTED}; font-size:12px;'>({title})</span>")
        self.lbl_title.setStyleSheet("font-size: 16px; color: #ffffff;")

        self.lbl_status = QLabel("SAFE")
        self.lbl_status.setStyleSheet("""
            background-color: rgba(46, 160, 67, 0.2);
            color: #3fb950;
            border: 1px solid #2ea043;
            border-radius: 6px;
            padding: 3px 10px;
            font-weight: bold;
            font-size: 11px;
        """)
        header_layout.addWidget(self.lbl_title)
        header_layout.addStretch()
        header_layout.addWidget(self.lbl_status)
        layout.addLayout(header_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet(f"background-color: {BORDER_COLOR}; max-height: 1px;")
        layout.addWidget(divider)

        # Primary Metrics Grid (Pressure & Temperature)
        metrics_grid = QGridLayout()
        metrics_grid.setSpacing(10)

        # Pressure metric
        lbl_p_tag = QLabel("PRESSURE")
        lbl_p_tag.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 1px;")
        self.lbl_pressure = QLabel("32.0 PSI")
        self.lbl_pressure.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        self.lbl_pressure_sub = QLabel("2.21 bar")
        self.lbl_pressure_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")

        metrics_grid.addWidget(lbl_p_tag, 0, 0)
        metrics_grid.addWidget(self.lbl_pressure, 1, 0)
        metrics_grid.addWidget(self.lbl_pressure_sub, 2, 0)

        # Temperature metric
        lbl_t_tag = QLabel("TEMPERATURE")
        lbl_t_tag.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 1px;")
        self.lbl_temp = QLabel("33.0 °C")
        self.lbl_temp.setStyleSheet("font-size: 24px; font-weight: bold; color: #ffffff;")
        self.lbl_temp_sub = QLabel("91.4 °F")
        self.lbl_temp_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")

        metrics_grid.addWidget(lbl_t_tag, 0, 1)
        metrics_grid.addWidget(self.lbl_temp, 1, 1)
        metrics_grid.addWidget(self.lbl_temp_sub, 2, 1)

        layout.addLayout(metrics_grid)

        # Predictive Risk Score & Health Bar
        risk_layout = QVBoxLayout()
        risk_header = QHBoxLayout()

        self.lbl_risk_label = QLabel("Risk: <b style='color:#3fb950;'>12%</b>")
        self.lbl_risk_label.setStyleSheet("font-size: 12px;")

        self.lbl_health_label = QLabel("Health: <b style='color:#58a6ff;'>88%</b>")
        self.lbl_health_label.setStyleSheet("font-size: 12px;")

        risk_header.addWidget(self.lbl_risk_label)
        risk_header.addStretch()
        risk_header.addWidget(self.lbl_health_label)
        risk_layout.addLayout(risk_header)

        self.progress_risk = QProgressBar()
        self.progress_risk.setRange(0, 100)
        self.progress_risk.setValue(12)
        self.progress_risk.setTextVisible(False)
        self.progress_risk.setFixedHeight(6)
        self.progress_risk.setStyleSheet("""
            QProgressBar {
                background-color: #21262d;
                border-radius: 3px;
            }
            QProgressBar::chunk {
                background-color: #3fb950;
                border-radius: 3px;
            }
        """)
        risk_layout.addWidget(self.progress_risk)
        layout.addLayout(risk_layout)

        # Prediction diagnosis text
        self.lbl_diagnosis = QLabel("Optimal pressure balance")
        self.lbl_diagnosis.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px; font-style: italic;")
        self.lbl_diagnosis.setWordWrap(True)
        layout.addWidget(self.lbl_diagnosis)

    def update_data(self, data: dict):
        """Updates tyre metrics and visual alerts."""
        p_psi = data.get("pressure_psi", 32.0)
        p_bar = data.get("pressure_bar", p_psi * 0.0689476)
        t_c = data.get("temperature_c", 32.0)
        t_f = data.get("temperature_f", t_c * 9 / 5 + 32)
        risk = data.get("risk_score", 10.0)
        health = data.get("health_pct", 90.0)
        status = data.get("status", "SAFE")
        prediction = data.get("prediction", "Optimal")

        # Format texts
        self.lbl_pressure.setText(f"{p_psi:.1f} PSI")
        self.lbl_pressure_sub.setText(f"{p_bar:.2f} bar")
        self.lbl_temp.setText(f"{t_c:.1f} °C")
        self.lbl_temp_sub.setText(f"{t_f:.1f} °F")

        # Color based on status
        color = get_status_color(status)

        self.lbl_status.setText(status)
        self.lbl_status.setStyleSheet(f"""
            background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25);
            color: {color};
            border: 1px solid {color};
            border-radius: 6px;
            padding: 3px 10px;
            font-weight: bold;
            font-size: 11px;
        """)

        # Border outline glow on card when not safe
        if status in ("WARNING", "CRITICAL"):
            self.setStyleSheet(f"""
                QFrame#card_{self.tyre_id} {{
                    background-color: {BG_CARD};
                    border: 2px solid {color};
                    border-radius: 12px;
                    padding: 12px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QFrame#card_{self.tyre_id} {{
                    background-color: {BG_CARD};
                    border: 2px solid {BORDER_COLOR};
                    border-radius: 12px;
                    padding: 12px;
                }}
            """)

        self.lbl_risk_label.setText(f"Risk: <b style='color:{color};'>{risk:.0f}%</b>")
        self.lbl_health_label.setText(f"Health: <b>{health:.0f}%</b>")
        self.progress_risk.setValue(int(risk))
        self.progress_risk.setStyleSheet(f"""
            QProgressBar {{
                background-color: #21262d;
                border-radius: 3px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 3px;
            }}
        """)

        self.lbl_diagnosis.setText(prediction)


class DashboardView(QWidget):
    """
    Main PTMS Dashboard Page containing top status KPIs and 4 Tyre cards.
    """

    quick_demo_clicked = Signal()
    reset_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(18)

        # Title & Subtitle Section
        title_bar = QHBoxLayout()
        title_col = QVBoxLayout()
        title_col.setSpacing(2)

        lbl_app_title = QLabel("PTMS")
        lbl_app_title.setStyleSheet(f"font-size: 26px; font-weight: 900; color: {COLOR_CYAN}; letter-spacing: 2px;")
        lbl_sub_title = QLabel("PREDICTIVE TYRE MONITORING SYSTEM")
        lbl_sub_title.setStyleSheet("font-size: 14px; font-weight: 600; color: #ffffff; letter-spacing: 1px;")

        title_col.addWidget(lbl_app_title)
        title_col.addWidget(lbl_sub_title)
        title_bar.addLayout(title_col)
        title_bar.addStretch()

        # Top Action Buttons
        btn_quick_demo = QPushButton("🚀 Run 12-Step Demo")
        btn_quick_demo.setProperty("class", "PrimaryBtn")
        btn_quick_demo.clicked.connect(self.quick_demo_clicked.emit)

        btn_reset = QPushButton("↺ Reset System")
        btn_reset.setProperty("class", "SecondaryBtn")
        btn_reset.clicked.connect(self.reset_clicked.emit)

        title_bar.addWidget(btn_quick_demo)
        title_bar.addWidget(btn_reset)
        main_layout.addLayout(title_bar)

        # Top System KPI Cards Grid
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(14)

        # 1. Vehicle Status
        self.card_vehicle_status = self._create_kpi_card("VEHICLE STATUS", "SAFE", "#3fb950", "Cruising 75 km/h")
        # 2. System Status
        self.card_system_status = self._create_kpi_card("SYSTEM STATUS", "OPERATIONAL", "#58a6ff", "All Subsystems Nominal")
        # 3. ESP32 Status
        self.card_esp32_status = self._create_kpi_card("ESP32 CONTROLLER", "ONLINE", "#3fb950", "240 MHz | 10 Hz Loop")
        # 4. Sensor Status
        self.card_sensor_status = self._create_kpi_card("SENSOR MESH", "4/4 ACTIVE", "#3fb950", "433 MHz RF Synchronized")
        # 5. Overall Tyre Health
        self.card_tyre_health = self._create_kpi_card("OVERALL HEALTH", "98%", "#3fb950", "Peak Dynamic Balance")

        kpi_grid.addWidget(self.card_vehicle_status["frame"], 0, 0)
        kpi_grid.addWidget(self.card_system_status["frame"], 0, 1)
        kpi_grid.addWidget(self.card_esp32_status["frame"], 0, 2)
        kpi_grid.addWidget(self.card_sensor_status["frame"], 0, 3)
        kpi_grid.addWidget(self.card_tyre_health["frame"], 0, 4)

        main_layout.addLayout(kpi_grid)

        # Active Alerts Banner Frame
        self.frame_alert = QFrame()
        self.frame_alert.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(46, 160, 67, 0.12);
                border: 1px solid #2ea043;
                border-radius: 8px;
                padding: 10px 16px;
            }}
        """)
        alert_layout = QHBoxLayout(self.frame_alert)
        alert_layout.setContentsMargins(12, 6, 12, 6)

        self.lbl_alert_icon = QLabel("🛡️")
        self.lbl_alert_icon.setStyleSheet("font-size: 18px;")
        self.lbl_alert_msg = QLabel("SYSTEM NOMINAL: All tyres operating within optimal pressure and temperature envelopes.")
        self.lbl_alert_msg.setStyleSheet("font-size: 13px; font-weight: 600; color: #ffffff;")

        alert_layout.addWidget(self.lbl_alert_icon)
        alert_layout.addWidget(self.lbl_alert_msg)
        alert_layout.addStretch()

        main_layout.addWidget(self.frame_alert)

        # Four Tyre Cards Grid (FL, FR, RL, RR)
        tyres_grid = QGridLayout()
        tyres_grid.setSpacing(16)

        self.card_fl = TyreStatusCard("FL", "Front Left")
        self.card_fr = TyreStatusCard("FR", "Front Right")
        self.card_rl = TyreStatusCard("RL", "Rear Left")
        self.card_rr = TyreStatusCard("RR", "Rear Right")

        tyres_grid.addWidget(self.card_fl, 0, 0)
        tyres_grid.addWidget(self.card_fr, 0, 1)
        tyres_grid.addWidget(self.card_rl, 1, 0)
        tyres_grid.addWidget(self.card_rr, 1, 1)

        main_layout.addLayout(tyres_grid)
        main_layout.addStretch()

    def _create_kpi_card(self, title: str, value: str, color: str, subtext: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)
        layout.setContentsMargins(10, 10, 10, 10)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet(f"color: {TEXT_MUTED}; font-size: 10px; font-weight: 600; letter-spacing: 0.5px;")

        lbl_val = QLabel(value)
        lbl_val.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")

        lbl_sub = QLabel(subtext)
        lbl_sub.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 11px;")

        layout.addWidget(lbl_title)
        layout.addWidget(lbl_val)
        layout.addWidget(lbl_sub)

        return {"frame": frame, "val": lbl_val, "sub": lbl_sub}

    def update_state(self, snapshot: dict):
        """Updates dashboard with latest digital twin state snapshot."""
        overall_status = snapshot.get("overall_status", "SAFE")
        health = snapshot.get("overall_health_pct", 98.0)
        active_alert = snapshot.get("active_alert")
        status_color = get_status_color(overall_status)

        # Update Top KPI Cards
        self.card_vehicle_status["val"].setText(overall_status)
        self.card_vehicle_status["val"].setStyleSheet(f"color: {status_color}; font-size: 20px; font-weight: bold;")

        self.card_tyre_health["val"].setText(f"{health:.0f}%")
        self.card_tyre_health["val"].setStyleSheet(f"color: {status_color}; font-size: 20px; font-weight: bold;")

        # Update Active Alert Banner
        if active_alert:
            self.frame_alert.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba({int(status_color[1:3], 16)}, {int(status_color[3:5], 16)}, {int(status_color[5:7], 16)}, 0.2);
                    border: 1px solid {status_color};
                    border-radius: 8px;
                    padding: 10px 16px;
                }}
            """)
            self.lbl_alert_icon.setText("⚠️" if overall_status in ("CAUTION", "WARNING") else "🚨")
            self.lbl_alert_msg.setText(f"ACTIVE ALERT: {active_alert} - INSPECTION RECOMMENDED")
        else:
            self.frame_alert.setStyleSheet(f"""
                QFrame {{
                    background-color: rgba(46, 160, 67, 0.12);
                    border: 1px solid #2ea043;
                    border-radius: 8px;
                    padding: 10px 16px;
                }}
            """)
            self.lbl_alert_icon.setText("🛡️")
            self.lbl_alert_msg.setText("SYSTEM NOMINAL: All tyres operating within optimal pressure and temperature envelopes.")

        # Update Tyre Cards
        tyres = snapshot.get("tyres", {})
        if "FL" in tyres:
            self.card_fl.update_data(tyres["FL"])
        if "FR" in tyres:
            self.card_fr.update_data(tyres["FR"])
        if "RL" in tyres:
            self.card_rl.update_data(tyres["RL"])
        if "RR" in tyres:
            self.card_rr.update_data(tyres["RR"])
