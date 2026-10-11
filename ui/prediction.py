"""
Predictive Tyre Monitoring System (PTMS) - Predictive Analysis Page
Deep trend analysis, rate derivatives (dP/dt, dT/dt), and early hazard forecasting.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QGridLayout, QProgressBar, QComboBox, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    get_status_color, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class PredictiveAnalysisView(QWidget):
    """
    Dedicated view for multi-factor predictive evaluation, trend slopes, and risk breakdown.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_tyre = "RL"

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        title_box = QHBoxLayout()
        col = QVBoxLayout()
        lbl_title = QLabel("PREDICTIVE ANALYSIS & TREND DIAGNOSTICS")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_CYAN}; letter-spacing: 1px;")
        lbl_sub = QLabel("Advanced multi-factor risk engine detecting anomalies before critical physical thresholds")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        col.addWidget(lbl_title)
        col.addWidget(lbl_sub)
        title_box.addLayout(col)
        title_box.addStretch()

        # Tyre Selector
        title_box.addWidget(QLabel("Select Tyre:"))
        self.combo_tyre = QComboBox()
        self.combo_tyre.addItems(["RL (Rear Left)", "FL (Front Left)", "FR (Front Right)", "RR (Rear Right)"])
        self.combo_tyre.currentIndexChanged.connect(self._on_tyre_changed)
        title_box.addWidget(self.combo_tyre)

        main_layout.addLayout(title_box)

        # Early Detection Educational Banner
        banner = QFrame()
        banner.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(56, 139, 253, 0.1);
                border: 1px solid rgba(56, 139, 253, 0.4);
                border-radius: 8px;
                padding: 12px 16px;
            }}
        """)
        b_layout = QHBoxLayout(banner)
        b_icon = QLabel("💡")
        b_icon.setStyleSheet("font-size: 22px;")
        b_text = QLabel(
            "<b>PREDICTIVE ADVANTAGE:</b> Standard direct TPMS only triggers when tyre pressure drops below 24 PSI (dangerous deflation). "
            "PTMS continuously evaluates <b>first derivatives (dP/dt, dT/dt)</b> and sidewall thermal coupling to identify slow leaks "
            "and impending failures <b>15 to 45 minutes in advance</b> while still at 30 PSI."
        )
        b_text.setWordWrap(True)
        b_text.setStyleSheet("font-size: 12px; color: #dcdcdc; line-height: 1.4;")
        b_layout.addWidget(b_icon)
        b_layout.addWidget(b_text, 1)
        main_layout.addWidget(banner)

        # Two Columns Layout: Left = Risk Score & Slopes; Right = Detailed Factor Matrix
        content_row = QHBoxLayout()
        content_row.setSpacing(16)

        # Left Column: Risk Gauge & Derivative Rates
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        # Risk Score Card
        self.card_risk = QFrame()
        self.card_risk.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 2px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        risk_layout = QVBoxLayout(self.card_risk)
        risk_layout.setSpacing(10)

        risk_hdr = QHBoxLayout()
        self.lbl_card_title = QLabel("REAR LEFT (RL) - PREDICTIVE RISK SCORE")
        self.lbl_card_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        self.lbl_status_badge = QLabel("SAFE")
        self.lbl_status_badge.setStyleSheet("""
            background-color: rgba(46, 160, 67, 0.2);
            color: #3fb950;
            border: 1px solid #2ea043;
            border-radius: 4px;
            padding: 4px 10px;
            font-weight: bold;
        """)
        risk_hdr.addWidget(self.lbl_card_title)
        risk_hdr.addStretch()
        risk_hdr.addWidget(self.lbl_status_badge)
        risk_layout.addLayout(risk_hdr)

        self.lbl_risk_score_huge = QLabel("12%")
        self.lbl_risk_score_huge.setStyleSheet("font-size: 42px; font-weight: 900; color: #3fb950;")
        risk_layout.addWidget(self.lbl_risk_score_huge)

        # Risk Bar
        self.bar_risk = QProgressBar()
        self.bar_risk.setRange(0, 100)
        self.bar_risk.setValue(12)
        self.bar_risk.setFixedHeight(10)
        self.bar_risk.setTextVisible(False)
        self.bar_risk.setStyleSheet("""
            QProgressBar {
                background-color: #21262d;
                border-radius: 5px;
            }
            QProgressBar::chunk {
                background-color: #3fb950;
                border-radius: 5px;
            }
        """)
        risk_layout.addWidget(self.bar_risk)

        # Risk Legend Scale
        scale_lbl = QLabel("0-20% SAFE  |  21-40% NORMAL  |  41-60% CAUTION  |  61-80% WARNING  |  81-100% CRITICAL")
        scale_lbl.setStyleSheet(f"font-size: 10px; color: {TEXT_MUTED}; text-align: center;")
        risk_layout.addWidget(scale_lbl)

        left_col.addWidget(self.card_risk)

        # Derivative Rates Grid
        rates_grid = QGridLayout()
        rates_grid.setSpacing(10)

        self.card_dp = self._create_metric_box("PRESSURE LOSS RATE (dP/dt)", "-0.02 PSI/min", "Linear regression slope")
        self.card_dt = self._create_metric_box("TEMPERATURE RATE (dT/dt)", "+0.01 °C/min", "Thermal acceleration")
        self.card_axle = self._create_metric_box("AXLE IMBALANCE (ΔP)", "0.2 PSI", "Deviation from peer tyre")
        self.card_var = self._create_metric_box("PRESSURE VARIANCE (σ²)", "0.004", "Signal stability index")

        rates_grid.addWidget(self.card_dp["frame"], 0, 0)
        rates_grid.addWidget(self.card_dt["frame"], 0, 1)
        rates_grid.addWidget(self.card_axle["frame"], 1, 0)
        rates_grid.addWidget(self.card_var["frame"], 1, 1)

        left_col.addLayout(rates_grid)
        content_row.addLayout(left_col, 5)

        # Right Column: Diagnostic Factor Breakdown & Predictive Advice
        right_col = QVBoxLayout()
        right_col.setSpacing(14)

        diag_frame = QFrame()
        diag_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 16px;
            }}
        """)
        d_layout = QVBoxLayout(diag_frame)
        d_layout.setSpacing(10)

        lbl_factors_title = QLabel("MULTI-FACTOR RISK DECOMPOSITION")
        lbl_factors_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        d_layout.addWidget(lbl_factors_title)

        # Factor Table
        self.table_factors = QTableWidget(5, 3)
        self.table_factors.setHorizontalHeaderLabels(["Risk Evaluation Factor", "Observed State", "Risk Impact"])
        self.table_factors.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_factors.verticalHeader().setVisible(False)
        self.table_factors.setStyleSheet(f"""
            QTableWidget {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_COLOR};
                border-radius: 6px;
            }}
        """)

        factors = [
            ("Absolute Pressure Deviation", "32.0 PSI (Nominal 32.0)", "+0% (Nominal)"),
            ("Predictive Leak Rate (dP/dt)", "-0.02 PSI/min (Normal)", "+0% (No leak detected)"),
            ("Thermal Operating Level", "33.2 °C (Safe < 50°C)", "+0% (Nominal)"),
            ("Sidewall Flex Coupling", "Low flex dissipation", "+0% (Nominal)"),
            ("Axle Symmetry Balance", "0.2 PSI vs RR", "+0% (Symmetric)")
        ]
        for row, (f_name, f_obs, f_imp) in enumerate(factors):
            self.table_factors.setItem(row, 0, QTableWidgetItem(f_name))
            self.table_factors.setItem(row, 1, QTableWidgetItem(f_obs))
            self.table_factors.setItem(row, 2, QTableWidgetItem(f_imp))

        d_layout.addWidget(self.table_factors)

        # Action Recommendation Box
        self.box_rec = QFrame()
        self.box_rec.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-left: 4px solid #2ea043;
                border-radius: 6px;
                padding: 10px 14px;
            }}
        """)
        rec_layout = QVBoxLayout(self.box_rec)
        rec_layout.setSpacing(4)
        rec_title = QLabel("RECOMMENDED ACTION & INTERVENTION:")
        rec_title.setStyleSheet("font-size: 11px; font-weight: bold; color: #ffffff;")
        self.lbl_rec_body = QLabel("All monitored parameters within safe engineering bounds. No inspection needed.")
        self.lbl_rec_body.setStyleSheet(f"font-size: 13px; color: {TEXT_PRIMARY};")
        rec_layout.addWidget(rec_title)
        rec_layout.addWidget(self.lbl_rec_body)

        d_layout.addWidget(self.box_rec)
        right_col.addWidget(diag_frame)
        content_row.addLayout(right_col, 5)

        main_layout.addLayout(content_row)
        main_layout.addStretch()

    def _create_metric_box(self, title: str, val: str, sub: str) -> dict:
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        layout = QVBoxLayout(frame)
        layout.setSpacing(4)

        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {TEXT_MUTED}; letter-spacing: 0.5px;")

        v_lbl = QLabel(val)
        v_lbl.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")

        s_lbl = QLabel(sub)
        s_lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")

        layout.addWidget(t_lbl)
        layout.addWidget(v_lbl)
        layout.addWidget(s_lbl)

        return {"frame": frame, "val": v_lbl, "sub": s_lbl}

    def _on_tyre_changed(self, idx: int):
        mapping = {0: "RL", 1: "FL", 2: "FR", 3: "RR"}
        self.selected_tyre = mapping.get(idx, "RL")

    def update_state(self, snapshot: dict):
        tyres = snapshot.get("tyres", {})
        data = tyres.get(self.selected_tyre, {})

        p = data.get("pressure_psi", 32.0)
        t = data.get("temperature_c", 33.0)
        risk = data.get("risk_score", 10.0)
        status = data.get("status", "SAFE")
        dp = data.get("pressure_rate_min", 0.0)
        dt = data.get("temp_rate_min", 0.0)
        axle = data.get("axle_delta_psi", 0.0)
        rec = data.get("recommendation", "Operating normally.")
        color = get_status_color(status)

        # Update card header
        self.lbl_card_title.setText(f"{self.selected_tyre} - PREDICTIVE RISK SCORE")
        self.lbl_risk_score_huge.setText(f"{risk:.0f}%")
        self.lbl_risk_score_huge.setStyleSheet(f"font-size: 42px; font-weight: 900; color: {color};")

        self.bar_risk.setValue(int(risk))
        self.bar_risk.setStyleSheet(f"""
            QProgressBar {{
                background-color: #21262d;
                border-radius: 5px;
            }}
            QProgressBar::chunk {{
                background-color: {color};
                border-radius: 5px;
            }}
        """)

        self.lbl_status_badge.setText(status)
        self.lbl_status_badge.setStyleSheet(f"""
            background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25);
            color: {color};
            border: 1px solid {color};
            border-radius: 4px;
            padding: 4px 10px;
            font-weight: bold;
        """)

        # Update metric boxes
        self.card_dp["val"].setText(f"{dp:+.2f} PSI/min")
        self.card_dp["val"].setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#f85149' if dp < -1.0 else '#ffffff'};")

        self.card_dt["val"].setText(f"{dt:+.2f} °C/min")
        self.card_dt["val"].setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#f85149' if dt > 2.0 else '#ffffff'};")

        self.card_axle["val"].setText(f"{axle:.2f} PSI")
        self.card_axle["val"].setStyleSheet(f"font-size: 18px; font-weight: bold; color: {'#d29922' if axle > 3.0 else '#ffffff'};")

        # Update table factor breakdown
        p_impact = "+0% (Nominal)"
        if p < 24.0:
            p_impact = "+50% (Severe deficit)"
        elif p < 28.0:
            p_impact = "+35% (Deficit)"
        elif p < 30.0:
            p_impact = "+18% (Mild deficit)"

        leak_impact = "+0% (Nominal)"
        if dp < -5.0:
            leak_impact = "+40% (Fast deflation)"
        elif dp < -1.0:
            leak_impact = "+26% (Slow leak active)"
        elif dp < -0.3:
            leak_impact = "+14% (Subtle drift)"

        temp_impact = "+0% (Safe)"
        if t > 80.0:
            temp_impact = "+45% (Thermal stress)"
        elif t > 65.0:
            temp_impact = "+25% (High heat)"
        elif dt > 1.5:
            temp_impact = "+15% (Accelerating)"

        flex_impact = "+18% (Coupled runaway)" if (p < 30.0 and (dt > 0.8 or t > 40.0)) else "+0% (Nominal)"
        axle_impact = f"+{20 if axle > 5.0 else (10 if axle > 3.0 else 0)}% ({axle:.1f} PSI diff)"

        self.table_factors.setItem(0, 1, QTableWidgetItem(f"{p:.1f} PSI"))
        self.table_factors.setItem(0, 2, QTableWidgetItem(p_impact))

        self.table_factors.setItem(1, 1, QTableWidgetItem(f"{dp:+.2f} PSI/min"))
        self.table_factors.setItem(1, 2, QTableWidgetItem(leak_impact))

        self.table_factors.setItem(2, 1, QTableWidgetItem(f"{t:.1f} °C"))
        self.table_factors.setItem(2, 2, QTableWidgetItem(temp_impact))

        self.table_factors.setItem(3, 1, QTableWidgetItem("Active" if (p < 30.0 and t > 40.0) else "Minimal"))
        self.table_factors.setItem(3, 2, QTableWidgetItem(flex_impact))

        self.table_factors.setItem(4, 1, QTableWidgetItem(f"{axle:.2f} PSI imbalance"))
        self.table_factors.setItem(4, 2, QTableWidgetItem(axle_impact))

        # Update recommendation box
        self.lbl_rec_body.setText(rec)
        self.box_rec.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border-left: 4px solid {color};
                border-radius: 6px;
                padding: 10px 14px;
            }}
        """)
