"""
Predictive Tyre Monitoring System (PTMS) - Main Application Window
Coordinates the unified sidebar navigation and single source-of-truth simulation engine.
"""

import os
import sys

# Ensure package directory is in sys.path regardless of how it is launched
_PKG_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PKG_ROOT not in sys.path:
    sys.path.insert(0, _PKG_ROOT)

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QButtonGroup,
    QStatusBar, QApplication
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QFont

from ui.styles import (
    GLOBAL_STYLESHEET, BG_DARK, BG_PANEL, BG_CARD, BORDER_COLOR,
    COLOR_CYAN, get_status_color, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)

from ui.dashboard import DashboardView
from ui.monitoring import LiveMonitoringView
from ui.vehicle_3d import Vehicle3DView
from ui.prediction import PredictiveAnalysisView
from ui.sensor_data import SensorDataView
from ui.simulation import SimulationControlView
from ui.history import HistoryView
from ui.system_info import SystemInfoView

from simulation.simulation_engine import SimulationEngine


class MainWindow(QMainWindow):
    """
    Main automotive control desktop shell with sidebar navigation.
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("PTMS - Predictive Tyre Monitoring System [Digital Twin Platform]")
        self.resize(1440, 920)
        self.setMinimumSize(1200, 780)

        # Set application icon
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets", "icons", "app_icon.png")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        # Apply global stylesheet
        self.setStyleSheet(GLOBAL_STYLESHEET)

        # Initialize Central Simulation Engine (Single Source of Truth)
        self.sim_engine = SimulationEngine(self)

        self._init_ui()
        self._connect_signals()

        # Start simulation loop
        self.sim_engine.start()

    def _init_ui(self):
        root_widget = QWidget()
        self.setCentralWidget(root_widget)

        root_layout = QHBoxLayout(root_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # 1. Left Sidebar Navigation
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(4)

        # App Brand / Logo Banner
        brand_frame = QFrame()
        brand_frame.setStyleSheet(f"""
            QFrame {{
                background-color: #0b0e14;
                border-bottom: 1px solid {BORDER_COLOR};
                padding: 16px 14px;
            }}
        """)
        b_layout = QVBoxLayout(brand_frame)
        b_layout.setSpacing(2)

        lbl_logo = QLabel("PTMS AUTO")
        lbl_logo.setStyleSheet(f"font-size: 18px; font-weight: 900; color: {COLOR_CYAN}; letter-spacing: 2px;")
        lbl_logo_sub = QLabel("PREDICTIVE TPMS TWIN")
        lbl_logo_sub.setStyleSheet(f"font-size: 10px; font-weight: 600; color: {TEXT_MUTED}; letter-spacing: 1px;")

        b_layout.addWidget(lbl_logo)
        b_layout.addWidget(lbl_logo_sub)
        s_layout.addWidget(brand_frame)

        # Navigation Buttons
        self.nav_group = QButtonGroup(self)
        self.nav_buttons = []

        nav_items = [
            ("📊  Dashboard", 0),
            ("🚗  Live Monitoring", 1),
            ("🧊  3D Vehicle CAD", 2),
            ("📈  Predictive Analysis", 3),
            ("⚡  Sensor Data", 4),
            ("🧪  Simulation", 5),
            ("🗄️  History Logs", 6),
            ("⚙️  System Information", 7),
        ]

        for text, index in nav_items:
            btn = QPushButton(text)
            btn.setCheckable(True)
            if index == 0:
                btn.setChecked(True)
            btn.clicked.connect(lambda _, idx=index: self._on_nav_clicked(idx))
            self.nav_group.addButton(btn)
            self.nav_buttons.append(btn)
            s_layout.addWidget(btn)

        s_layout.addStretch()

        # Sidebar Hardware Quick Status Pill
        hw_pill = QFrame()
        hw_pill.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                margin: 12px;
                padding: 10px;
            }}
        """)
        p_layout = QVBoxLayout(hw_pill)
        p_layout.setSpacing(4)
        lbl_esp = QLabel("ESP32: <b>ONLINE</b> (240 MHz)")
        lbl_esp.setStyleSheet("font-size: 11px; color: #3fb950;")
        lbl_rf = QLabel("RF TPMS: <b>433.92 MHz OK</b>")
        lbl_rf.setStyleSheet(f"font-size: 11px; color: {TEXT_SECONDARY};")
        p_layout.addWidget(lbl_esp)
        p_layout.addWidget(lbl_rf)
        s_layout.addWidget(hw_pill)

        root_layout.addWidget(sidebar)

        # 2. Right Main Content Area
        right_container = QWidget()
        right_layout = QVBoxLayout(right_container)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        # Top Universal Status Header Bar
        top_bar = QFrame()
        top_bar.setObjectName("headerBar")
        top_bar.setFixedHeight(54)
        tb_layout = QHBoxLayout(top_bar)
        tb_layout.setContentsMargins(20, 8, 20, 8)
        tb_layout.setSpacing(14)

        self.lbl_top_vehicle_status = QLabel("VEHICLE: SAFE")
        self.lbl_top_vehicle_status.setStyleSheet("""
            background-color: rgba(46, 160, 67, 0.2);
            color: #3fb950;
            border: 1px solid #2ea043;
            border-radius: 6px;
            padding: 4px 12px;
            font-weight: bold;
            font-size: 12px;
        """)
        tb_layout.addWidget(self.lbl_top_vehicle_status)

        self.lbl_top_alert = QLabel("All 4 Wheel Nodes Nominal")
        self.lbl_top_alert.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")
        tb_layout.addWidget(self.lbl_top_alert)

        tb_layout.addStretch()

        # Quick Demo & Reset in Header
        btn_header_demo = QPushButton("🚀 Run 12-Step Demo")
        btn_header_demo.setProperty("class", "PrimaryBtn")
        btn_header_demo.clicked.connect(self._run_12_step_demo)
        tb_layout.addWidget(btn_header_demo)

        btn_header_reset = QPushButton("↺ Reset")
        btn_header_reset.setProperty("class", "SecondaryBtn")
        btn_header_reset.clicked.connect(self._reset_system)
        tb_layout.addWidget(btn_header_reset)

        right_layout.addWidget(top_bar)

        # Central Stacked Pages (8 pages)
        self.stacked_widget = QStackedWidget()

        # Instantiate 8 Views
        self.page_dashboard = DashboardView()
        self.page_monitoring = LiveMonitoringView()
        self.page_3d = Vehicle3DView()
        self.page_prediction = PredictiveAnalysisView()
        self.page_graphs = SensorDataView()
        self.page_simulation = SimulationControlView()
        self.page_history = HistoryView()
        self.page_system_info = SystemInfoView()

        self.stacked_widget.addWidget(self.page_dashboard)      # 0
        self.stacked_widget.addWidget(self.page_monitoring)     # 1
        self.stacked_widget.addWidget(self.page_3d)             # 2
        self.stacked_widget.addWidget(self.page_prediction)     # 3
        self.stacked_widget.addWidget(self.page_graphs)         # 4
        self.stacked_widget.addWidget(self.page_simulation)     # 5
        self.stacked_widget.addWidget(self.page_history)        # 6
        self.stacked_widget.addWidget(self.page_system_info)    # 7

        right_layout.addWidget(self.stacked_widget, 1)
        root_layout.addWidget(right_container, 1)

    def _connect_signals(self):
        # Connect Simulation Engine to all 8 pages
        self.sim_engine.data_updated.connect(self._on_telemetry_tick)

        # Connect Dashboard buttons
        self.page_dashboard.quick_demo_clicked.connect(self._run_12_step_demo)
        self.page_dashboard.reset_clicked.connect(self._reset_system)

        # Connect Simulation page controls
        self.page_simulation.fault_applied.connect(self.sim_engine.set_fault)
        self.page_simulation.speed_changed.connect(self.sim_engine.set_speed)
        self.page_simulation.reset_requested.connect(self._reset_system)
        self.page_simulation.demo_start_requested.connect(self.sim_engine.start_demonstration)
        self.page_simulation.demo_stop_requested.connect(self.sim_engine.stop_demonstration)

    def _on_nav_clicked(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 6:  # History page
            self.page_history.refresh_data()

    def _on_telemetry_tick(self, snapshot: dict):
        """Dispatches single source-of-truth snapshot to every page in real time."""
        overall_status = snapshot.get("overall_status", "SAFE")
        color = get_status_color(overall_status)
        active_alert = snapshot.get("active_alert")

        # Update Top Status Bar
        self.lbl_top_vehicle_status.setText(f"VEHICLE: {overall_status}")
        self.lbl_top_vehicle_status.setStyleSheet(f"""
            background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25);
            color: {color};
            border: 1px solid {color};
            border-radius: 6px;
            padding: 4px 12px;
            font-weight: bold;
            font-size: 12px;
        """)

        if active_alert:
            self.lbl_top_alert.setText(f"⚠️ {active_alert} - INSPECTION RECOMMENDED")
            self.lbl_top_alert.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 12px;")
        else:
            self.lbl_top_alert.setText("All 4 Wheel Nodes Nominal (433 MHz Sync)")
            self.lbl_top_alert.setStyleSheet(f"color: {TEXT_SECONDARY}; font-size: 12px;")

        # Update each page
        self.page_dashboard.update_state(snapshot)
        self.page_monitoring.update_state(snapshot)
        self.page_3d.update_state(snapshot)
        self.page_prediction.update_state(snapshot)
        self.page_graphs.update_state(snapshot)
        self.page_simulation.update_state(snapshot)
        self.page_system_info.update_state(snapshot)

    def _run_12_step_demo(self):
        # Switch to 3D Vehicle CAD page or Simulation page and trigger demo
        self.sim_engine.start_demonstration()
        self.nav_buttons[2].setChecked(True)
        self.stacked_widget.setCurrentIndex(2)

    def _reset_system(self):
        self.sim_engine.reset_all_tyres()
