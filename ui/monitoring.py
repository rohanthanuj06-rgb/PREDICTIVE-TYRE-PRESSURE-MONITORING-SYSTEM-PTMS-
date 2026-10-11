"""
Predictive Tyre Monitoring System (PTMS) - Live Monitoring View
Features an interactive 2D top-view vehicle blueprint with real-time animated
telemetry beacons and wheel status cards.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QScrollArea
)
from PySide6.QtCore import Qt, QTimer, QPointF, QRectF
from PySide6.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QRadialGradient, QLinearGradient
)

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    get_status_color, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class VehicleTopViewWidget(QWidget):
    """
    Renders an automotive CAD schematic top-view of the vehicle chassis,
    axles, wheels, and ESP32 central node with animated telemetry waves.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(420, 520)

        self.tyre_statuses = {
            "FL": {"status": "SAFE", "p": 32.0, "t": 33.0, "risk": 10.0},
            "FR": {"status": "SAFE", "p": 32.0, "t": 33.0, "risk": 10.0},
            "RL": {"status": "SAFE", "p": 32.0, "t": 33.0, "risk": 10.0},
            "RR": {"status": "SAFE", "p": 32.0, "t": 33.0, "risk": 10.0}
        }
        self.selected_tyre = "RL"

        # Animation phase for pulsing halos
        self.pulse_phase = 0.0
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_step)
        self.anim_timer.start(50)  # 20 FPS pulse animation

    def _animate_step(self):
        self.pulse_phase = (self.pulse_phase + 0.08) % (2 * 3.14159)
        self.update()

    def update_telemetry(self, tyres_data: dict):
        for tid in ("FL", "FR", "RL", "RR"):
            if tid in tyres_data:
                d = tyres_data[tid]
                self.tyre_statuses[tid] = {
                    "status": d.get("status", "SAFE"),
                    "p": d.get("pressure_psi", 32.0),
                    "t": d.get("temperature_c", 33.0),
                    "risk": d.get("risk_score", 10.0)
                }
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w / 2.0
        cy = h / 2.0

        # Draw grid background
        pen_grid = QPen(QColor(BORDER_COLOR), 0.5, Qt.DotLine)
        painter.setPen(pen_grid)
        for x in range(0, w, 30):
            painter.drawLine(x, 0, x, h)
        for y in range(0, h, 30):
            painter.drawLine(0, y, w, y)

        # Scale parameters for vehicle
        v_width = 170.0
        v_length = 360.0

        # Draw Chassis Silhouette
        car_rect = QRectF(cx - v_width / 2.0, cy - v_length / 2.0, v_width, v_length)
        body_grad = QLinearGradient(car_rect.topLeft(), car_rect.bottomRight())
        body_grad.setColorAt(0.0, QColor("#1c232e"))
        body_grad.setColorAt(0.5, QColor("#13171d"))
        body_grad.setColorAt(1.0, QColor("#1c232e"))

        pen_body = QPen(QColor("#388bfd"), 1.8)
        painter.setPen(pen_body)
        painter.setBrush(QBrush(body_grad))
        painter.drawRoundedRect(car_rect, 45, 45)

        # Windshield and cabin outline
        cabin_rect = QRectF(cx - 62, cy - 80, 124, 150)
        painter.setPen(QPen(QColor("#2d333b"), 1.2))
        painter.setBrush(QBrush(QColor("#0d1117")))
        painter.drawRoundedRect(cabin_rect, 25, 25)

        # Axles
        painter.setPen(QPen(QColor("#484f58"), 3.0))
        painter.drawLine(cx - 85, cy - 110, cx + 85, cy - 110)  # Front axle
        painter.drawLine(cx - 85, cy + 110, cx + 85, cy + 110)  # Rear axle

        # Center ESP32 Controller Unit
        esp_rect = QRectF(cx - 24, cy - 15, 48, 30)
        painter.setPen(QPen(QColor(COLOR_CYAN), 1.5))
        painter.setBrush(QBrush(QColor("#161b22")))
        painter.drawRoundedRect(esp_rect, 4, 4)

        painter.setPen(QPen(QColor(COLOR_CYAN)))
        painter.setFont(QFont("Segoe UI", 8, QFont.Bold))
        painter.drawText(esp_rect, Qt.AlignCenter, "ESP32")

        # Telemetry signal traces from ESP32 to wheels
        self._draw_signal_traces(painter, cx, cy)

        # Four Wheels positions
        # FL: Top Left, FR: Top Right, RL: Bottom Left, RR: Bottom Right
        wheel_coords = {
            "FL": (cx - 96, cy - 110),
            "FR": (cx + 96, cy - 110),
            "RL": (cx - 96, cy + 110),
            "RR": (cx + 96, cy + 110)
        }

        for tid, (wx, wy) in wheel_coords.items():
            self._draw_wheel(painter, tid, wx, wy)

    def _draw_signal_traces(self, painter: QPainter, cx: float, cy: float):
        """Draws animated pulse lines between central ESP32 and wheels."""
        pulse_alpha = int(120 + 80 * (0.5 + 0.5 * (self.pulse_phase % 3.14)))
        pen_trace = QPen(QColor(56, 139, 253, pulse_alpha), 1.2, Qt.DashLine)
        painter.setPen(pen_trace)

        wheel_targets = [
            (cx - 85, cy - 110),
            (cx + 85, cy - 110),
            (cx - 85, cy + 110),
            (cx + 85, cy + 110)
        ]
        for wx, wy in wheel_targets:
            painter.drawLine(cx, cy, wx, wy)

    def _draw_wheel(self, painter: QPainter, tid: str, wx: float, wy: float):
        w_width = 30.0
        w_height = 68.0
        rect = QRectF(wx - w_width / 2.0, wy - w_height / 2.0, w_width, w_height)

        data = self.tyre_statuses.get(tid, {"status": "SAFE", "p": 32.0, "t": 33.0})
        status = data["status"]
        color_hex = get_status_color(status)
        qc = QColor(color_hex)

        # Halo glow if warning or critical or selected
        is_alert = status in ("WARNING", "CRITICAL")
        if is_alert or tid == self.selected_tyre:
            halo_size = 18.0 + 6.0 * (0.5 + 0.5 * (self.pulse_phase % 3.14))
            rad_grad = QRadialGradient(wx, wy, halo_size + 20)
            rad_grad.setColorAt(0.0, QColor(qc.red(), qc.green(), qc.blue(), 120))
            rad_grad.setColorAt(1.0, QColor(qc.red(), qc.green(), qc.blue(), 0))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(rad_grad))
            painter.drawEllipse(QPointF(wx, wy), halo_size + 20, halo_size + 25)

        # Tyre rubber body
        painter.setPen(QPen(qc, 2.0 if tid == self.selected_tyre else 1.2))
        painter.setBrush(QBrush(QColor("#090d13")))
        painter.drawRoundedRect(rect, 8, 8)

        # Rim inner rectangle
        rim_rect = QRectF(wx - 8, wy - 22, 16, 44)
        painter.setPen(QPen(QColor("#484f58"), 1.0))
        painter.setBrush(QBrush(QColor("#21262d")))
        painter.drawRoundedRect(rim_rect, 4, 4)

        # Tyre label
        painter.setFont(QFont("Segoe UI", 9, QFont.Bold))
        painter.setPen(QPen(QColor("#ffffff")))
        painter.drawText(QRectF(wx - 25, wy - 30, 50, 16), Qt.AlignCenter, tid)

        # Pressure tag inside wheel
        painter.setFont(QFont("Segoe UI", 7, QFont.Bold))
        painter.setPen(QPen(qc))
        painter.drawText(QRectF(wx - 25, wy + 16, 50, 14), Qt.AlignCenter, f"{data['p']:.0f} PSI")


class LiveMonitoringView(QWidget):
    """
    Live Monitoring Page with Interactive 2D Blueprint and Detailed Real-Time Cards.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 16, 20, 16)
        main_layout.setSpacing(20)

        # Left Column: Interactive Vehicle Blueprint
        left_panel = QFrame()
        left_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 14px;
            }}
        """)
        left_layout = QVBoxLayout(left_panel)

        lbl_bp_title = QLabel("AUTOMOTIVE TELEMETRY BLUEPRINT")
        lbl_bp_title.setStyleSheet(f"font-size: 13px; font-weight: bold; color: {COLOR_CYAN}; letter-spacing: 1px;")
        lbl_bp_sub = QLabel("Real-time RF sensor acquisition & dynamic thermal mapping")
        lbl_bp_sub.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")

        left_layout.addWidget(lbl_bp_title)
        left_layout.addWidget(lbl_bp_sub)

        self.vehicle_blueprint = VehicleTopViewWidget()
        left_layout.addWidget(self.vehicle_blueprint, 1)

        main_layout.addWidget(left_panel, 3)

        # Right Column: 4 Real-Time Detailed Cards
        right_panel = QFrame()
        right_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 16px;
            }}
        """)
        right_layout = QVBoxLayout(right_panel)
        right_layout.setSpacing(14)

        lbl_cards_title = QLabel("REAL-TIME WHEEL NODES")
        lbl_cards_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        right_layout.addWidget(lbl_cards_title)

        self.wheel_cards = {}
        for tid, name in (("FL", "FRONT LEFT"), ("FR", "FRONT RIGHT"), ("RL", "REAR LEFT"), ("RR", "REAR RIGHT")):
            card = self._create_monitoring_card(tid, name)
            self.wheel_cards[tid] = card
            right_layout.addWidget(card["frame"])

        right_layout.addStretch()
        main_layout.addWidget(right_panel, 4)

    def _create_monitoring_card(self, tid: str, name: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px 14px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(6)

        # Header row
        hdr = QHBoxLayout()
        lbl_name = QLabel(f"<b>{tid}</b> - {name}")
        lbl_name.setStyleSheet("font-size: 13px; color: #ffffff;")

        lbl_status = QLabel("SAFE")
        lbl_status.setStyleSheet("color: #3fb950; font-weight: bold; font-size: 11px;")

        hdr.addWidget(lbl_name)
        hdr.addStretch()
        hdr.addWidget(lbl_status)
        layout.addLayout(hdr)

        # Metrics row
        row = QHBoxLayout()

        lbl_p = QLabel("32.0 PSI")
        lbl_p.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")

        lbl_t = QLabel("33.0 °C")
        lbl_t.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")

        lbl_risk = QLabel("Risk: 10%")
        lbl_risk.setStyleSheet("font-size: 13px; color: #3fb950;")

        row.addWidget(lbl_p)
        row.addSpacing(16)
        row.addWidget(lbl_t)
        row.addSpacing(16)
        row.addWidget(lbl_risk)
        row.addStretch()
        layout.addLayout(row)

        lbl_rates = QLabel("dP/dt: 0.00 PSI/min  |  dT/dt: 0.00 °C/min")
        lbl_rates.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        layout.addWidget(lbl_rates)

        return {
            "frame": frame,
            "status": lbl_status,
            "p": lbl_p,
            "t": lbl_t,
            "risk": lbl_risk,
            "rates": lbl_rates
        }

    def update_state(self, snapshot: dict):
        tyres = snapshot.get("tyres", {})
        self.vehicle_blueprint.update_telemetry(tyres)

        for tid, card in self.wheel_cards.items():
            if tid in tyres:
                d = tyres[tid]
                p = d.get("pressure_psi", 32.0)
                t = d.get("temperature_c", 33.0)
                risk = d.get("risk_score", 10.0)
                status = d.get("status", "SAFE")
                dp = d.get("pressure_rate_min", 0.0)
                dt = d.get("temp_rate_min", 0.0)
                color = get_status_color(status)

                card["status"].setText(status)
                card["status"].setStyleSheet(f"color: {color}; font-weight: bold; font-size: 11px;")
                card["p"].setText(f"{p:.1f} PSI")
                card["t"].setText(f"{t:.1f} °C")
                card["risk"].setText(f"Risk: {risk:.0f}%")
                card["risk"].setStyleSheet(f"color: {color}; font-weight: bold;")
                card["rates"].setText(f"dP/dt: {dp:+.2f} PSI/min  |  dT/dt: {dt:+.2f} °C/min")

                if status in ("WARNING", "CRITICAL"):
                    card["frame"].setStyleSheet(f"""
                        QFrame {{
                            background-color: {BG_PANEL};
                            border: 1px solid {color};
                            border-radius: 8px;
                            padding: 10px 14px;
                        }}
                    """)
                else:
                    card["frame"].setStyleSheet(f"""
                        QFrame {{
                            background-color: {BG_PANEL};
                            border: 1px solid {BORDER_COLOR};
                            border-radius: 8px;
                            padding: 10px 14px;
                        }}
                    """)
