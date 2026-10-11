"""
Predictive Tyre Monitoring System (PTMS) - Simulation & Automated Demo Control Center
Allows:
- Manual fault injection (modes, tyre selection, severity 0-100%, sim speeds 0.5x-5x)
- 12-Step Automated Demonstration sequence with real-time progress & narrative explanation
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QSlider, QProgressBar, QGridLayout,
    QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class SimulationControlView(QWidget):
    """
    Simulation control page for fault injection and the 12-step demo sequencer.
    """

    fault_applied = Signal(str, str, float)  # tyre_id, fault_mode, severity
    speed_changed = Signal(float)            # speed_multiplier
    reset_requested = Signal()
    demo_start_requested = Signal()
    demo_stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 20, 24, 20)
        main_layout.setSpacing(16)

        # Header Title
        title_box = QVBoxLayout()
        lbl_title = QLabel("SIMULATION ENGINE & FAULT INJECTION LABORATORY")
        lbl_title.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {COLOR_CYAN};")
        lbl_sub = QLabel("Simulate pneumatic tyre faults, thermodynamic degradation, and automated validation scenarios")
        lbl_sub.setStyleSheet(f"font-size: 12px; color: {TEXT_MUTED};")
        title_box.addWidget(lbl_title)
        title_box.addWidget(lbl_sub)
        main_layout.addLayout(title_box)

        # Two Main Panels: Left = Manual Controls; Right = 12-Step Automated Demo
        cols_layout = QHBoxLayout()
        cols_layout.setSpacing(18)

        # --- LEFT PANEL: Manual Fault Injection ---
        manual_frame = QFrame()
        manual_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 18px;
            }}
        """)
        m_layout = QVBoxLayout(manual_frame)
        m_layout.setSpacing(14)

        lbl_m_hdr = QLabel("MANUAL FAULT INJECTION CONTROLS")
        lbl_m_hdr.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        m_layout.addWidget(lbl_m_hdr)

        # Target Tyre Selector
        t_row = QHBoxLayout()
        t_row.addWidget(QLabel("Target Wheel:"))
        self.combo_target_tyre = QComboBox()
        self.combo_target_tyre.addItems(["RL (Rear Left)", "FL (Front Left)", "FR (Front Right)", "RR (Rear Right)"])
        t_row.addWidget(self.combo_target_tyre, 1)
        m_layout.addLayout(t_row)

        # Fault Mode Selector
        f_row = QHBoxLayout()
        f_row.addWidget(QLabel("Simulation Mode:"))
        self.combo_fault_mode = QComboBox()
        self.combo_fault_mode.addItems([
            "NORMAL (Nominal Pressure & Temp)",
            "SLOW LEAK (Pinhole / Valve degradation)",
            "RAPID LEAK (Puncture Blowout Risk)",
            "LOW PRESSURE (Under-inflated Cold Tyre)",
            "HIGH PRESSURE (Over-inflated Tyre)",
            "OVERHEATING (Brake Drag / Bearing Friction)",
            "COMBINED FAULT (Leak + Extreme Thermal Rise)"
        ])
        f_row.addWidget(self.combo_fault_mode, 1)
        m_layout.addLayout(f_row)

        # Severity Slider (0 - 100%)
        m_layout.addWidget(QLabel("Fault Severity (0% to 100%):"))
        self.lbl_severity_val = QLabel("50%")
        self.lbl_severity_val.setStyleSheet("font-size: 16px; font-weight: bold; color: #58a6ff;")

        self.slider_severity = QSlider(Qt.Horizontal)
        self.slider_severity.setRange(0, 100)
        self.slider_severity.setValue(50)
        self.slider_severity.valueChanged.connect(lambda v: self.lbl_severity_val.setText(f"{v}%"))

        s_box = QHBoxLayout()
        s_box.addWidget(self.slider_severity, 1)
        s_box.addWidget(self.lbl_severity_val)
        m_layout.addLayout(s_box)

        # Simulation Speed Multipliers (0.5x, 1x, 2x, 5x)
        m_layout.addWidget(QLabel("Simulation Execution Speed:"))
        speed_row = QHBoxLayout()
        self.speed_btns = {}
        for sp in (0.5, 1.0, 2.0, 5.0):
            btn = QPushButton(f"{sp}x")
            btn.setProperty("class", "SecondaryBtn")
            if sp == 1.0:
                btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold;")
            btn.clicked.connect(lambda _, s=sp: self._on_speed_clicked(s))
            self.speed_btns[sp] = btn
            speed_row.addWidget(btn)
        m_layout.addLayout(speed_row)

        # Action Buttons
        btn_apply = QPushButton("⚡ INJECT FAULT")
        btn_apply.setProperty("class", "PrimaryBtn")
        btn_apply.setStyleSheet("padding: 10px; font-size: 14px;")
        btn_apply.clicked.connect(self._on_apply_fault)
        m_layout.addWidget(btn_apply)

        btn_reset_manual = QPushButton("↺ RESET ALL TYRES TO NOMINAL")
        btn_reset_manual.setProperty("class", "SecondaryBtn")
        btn_reset_manual.setStyleSheet("padding: 8px;")
        btn_reset_manual.clicked.connect(self.reset_requested.emit)
        m_layout.addWidget(btn_reset_manual)

        m_layout.addStretch()
        cols_layout.addWidget(manual_frame, 4)

        # --- RIGHT PANEL: 12-Step Automated Demonstration ---
        demo_frame = QFrame()
        demo_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 12px;
                padding: 18px;
            }}
        """)
        d_layout = QVBoxLayout(demo_frame)
        d_layout.setSpacing(12)

        d_hdr = QHBoxLayout()
        lbl_d_title = QLabel("AUTOMATED 12-STEP DEMONSTRATION SEQUENCER")
        lbl_d_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        d_hdr.addWidget(lbl_d_title)
        d_hdr.addStretch()

        self.btn_run_demo = QPushButton("▶ START DEMO")
        self.btn_run_demo.setProperty("class", "PrimaryBtn")
        self.btn_run_demo.clicked.connect(self._toggle_demo_state)
        d_hdr.addWidget(self.btn_run_demo)
        d_layout.addLayout(d_hdr)

        # Progress bar for overall steps
        self.lbl_demo_progress_hdr = QLabel("Demo Progress: Step 0 of 12 (Standby)")
        self.lbl_demo_progress_hdr.setStyleSheet(f"font-size: 12px; color: {COLOR_CYAN}; font-weight: bold;")
        d_layout.addWidget(self.lbl_demo_progress_hdr)

        self.bar_demo = QProgressBar()
        self.bar_demo.setRange(0, 12)
        self.bar_demo.setValue(0)
        self.bar_demo.setFixedHeight(8)
        self.bar_demo.setTextVisible(False)
        self.bar_demo.setStyleSheet("""
            QProgressBar {
                background-color: #21262d;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: #58a6ff;
                border-radius: 4px;
            }
        """)
        d_layout.addWidget(self.bar_demo)

        # Active Step Narrative Box
        self.step_narrative_box = QFrame()
        self.step_narrative_box.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 2px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 14px;
            }}
        """)
        s_narrative_layout = QVBoxLayout(self.step_narrative_box)
        s_narrative_layout.setSpacing(6)

        self.lbl_active_step_title = QLabel("Step Standby: Click 'Start Demo' to begin")
        self.lbl_active_step_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")

        self.lbl_active_step_desc = QLabel(
            "This automated sequence showcases the end-to-end hardware-software pipeline: "
            "Safe baseline ➔ Slow leak injection ➔ Trend detection ➔ Risk score escalation ➔ "
            "3D visual highlighting ➔ OLED screen update ➔ LED / Buzzer alarms ➔ Inspection warning."
        )
        self.lbl_active_step_desc.setWordWrap(True)
        self.lbl_active_step_desc.setStyleSheet(f"font-size: 12px; color: {TEXT_SECONDARY}; line-height: 1.4;")

        s_narrative_layout.addWidget(self.lbl_active_step_title)
        s_narrative_layout.addWidget(self.lbl_active_step_desc)
        d_layout.addWidget(self.step_narrative_box)

        # Steps checklist scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        steps_container = QWidget()
        self.steps_vbox = QVBoxLayout(steps_container)
        self.steps_vbox.setSpacing(6)

        # 12 steps descriptions
        steps_summary = [
            ("Step 1", "All tyres SAFE (Nominal baseline)"),
            ("Step 2", "RL tyre develops slow pressure leakage"),
            ("Step 3", "Pressure gradually decreases"),
            ("Step 4", "Temperature gradually increases (Sidewall flex)"),
            ("Step 5", "Trend analysis detects abnormal behaviour (dP/dt < 0)"),
            ("Step 6", "Risk score increases (0-100% evaluation)"),
            ("Step 7", "RL changes SAFE ➔ CAUTION ➔ WARNING"),
            ("Step 8", "3D RL tyre changes to warning indication"),
            ("Step 9", "Virtual OLED updates"),
            ("Step 10", "Red/yellow indicators activate according to severity"),
            ("Step 11", "Buzzer activates at critical state"),
            ("Step 12", "System displays: 'PREDICTED TYRE FAILURE RISK'")
        ]

        self.step_widgets = []
        for s_num, s_desc in steps_summary:
            f = QFrame()
            f.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_PANEL};
                    border: 1px solid {BORDER_COLOR};
                    border-radius: 6px;
                    padding: 6px 10px;
                }}
            """)
            l = QHBoxLayout(f)
            l.setContentsMargins(6, 4, 6, 4)
            lbl_s = QLabel(f"<b>{s_num}:</b> {s_desc}")
            lbl_s.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
            l.addWidget(lbl_s)
            self.steps_vbox.addWidget(f)
            self.step_widgets.append((f, lbl_s))

        scroll.setWidget(steps_container)
        d_layout.addWidget(scroll, 1)

        cols_layout.addWidget(demo_frame, 6)
        main_layout.addLayout(cols_layout)

    def _on_speed_clicked(self, speed: float):
        for s, btn in self.speed_btns.items():
            if s == speed:
                btn.setStyleSheet("background-color: #1f6feb; color: white; font-weight: bold;")
            else:
                btn.setStyleSheet("")
        self.speed_changed.emit(speed)

    def _on_apply_fault(self):
        tyre_map = {0: "RL", 1: "FL", 2: "FR", 3: "RR"}
        mode_map = {
            0: "NORMAL",
            1: "SLOW_LEAK",
            2: "RAPID_LEAK",
            3: "LOW_PRESSURE",
            4: "HIGH_PRESSURE",
            5: "OVERHEATING",
            6: "COMBINED_FAULT"
        }
        tid = tyre_map.get(self.combo_target_tyre.currentIndex(), "RL")
        f_mode = mode_map.get(self.combo_fault_mode.currentIndex(), "SLOW_LEAK")
        sev = self.slider_severity.value() / 100.0

        self.fault_applied.emit(tid, f_mode, sev)

    def _toggle_demo_state(self):
        if self.btn_run_demo.text().startswith("▶"):
            self.demo_start_requested.emit()
            self.btn_run_demo.setText("⏹ STOP DEMO")
            self.btn_run_demo.setStyleSheet("background-color: #f85149; color: white;")
        else:
            self.demo_stop_requested.emit()
            self.btn_run_demo.setText("▶ START DEMO")
            self.btn_run_demo.setStyleSheet("")

    def update_state(self, snapshot: dict):
        demo = snapshot.get("demo_state", {})
        is_active = demo.get("active", False)
        step_idx = demo.get("step_index", 0)
        total_steps = demo.get("total_steps", 12)
        step_title = demo.get("step_title", "")
        step_desc = demo.get("step_desc", "")

        if is_active:
            self.btn_run_demo.setText("⏹ STOP DEMO")
            self.btn_run_demo.setStyleSheet("background-color: #f85149; color: white;")
            self.lbl_demo_progress_hdr.setText(f"Demo Active: Step {step_idx} of {total_steps}")
            self.bar_demo.setValue(step_idx)
            self.lbl_active_step_title.setText(f"Step {step_idx}: {step_title}")
            self.lbl_active_step_desc.setText(step_desc)

            self.step_narrative_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_PANEL};
                    border: 2px solid {COLOR_CYAN};
                    border-radius: 8px;
                    padding: 14px;
                }}
            """)

            # Highlight current step in checklist
            for i, (frame, lbl) in enumerate(self.step_widgets):
                if i + 1 == step_idx:
                    frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: rgba(56, 139, 253, 0.25);
                            border: 1px solid #388bfd;
                            border-radius: 6px;
                            padding: 6px 10px;
                        }}
                    """)
                    lbl.setStyleSheet("font-size: 11px; color: #ffffff; font-weight: bold;")
                elif i + 1 < step_idx:
                    frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: rgba(46, 160, 67, 0.15);
                            border: 1px solid #2ea043;
                            border-radius: 6px;
                            padding: 6px 10px;
                        }}
                    """)
                    lbl.setStyleSheet("font-size: 11px; color: #3fb950;")
                else:
                    frame.setStyleSheet(f"""
                        QFrame {{
                            background-color: {BG_PANEL};
                            border: 1px solid {BORDER_COLOR};
                            border-radius: 6px;
                            padding: 6px 10px;
                        }}
                    """)
                    lbl.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        else:
            self.btn_run_demo.setText("▶ START DEMO")
            self.btn_run_demo.setStyleSheet("")
            if self.bar_demo.value() == 12:
                self.lbl_demo_progress_hdr.setText("Demo Completed: All 12 Steps Successfully Validated!")
            else:
                self.lbl_demo_progress_hdr.setText("Demo Progress: Standby")
