"""
Predictive Tyre Monitoring System (PTMS) - Embedded 3D Vehicle Page
Embeds interactive CAD-style prototype assembly directly into PySide6 via PyVistaQt.
Features:
- Full 3D vehicle prototype model (Chassis, 4 Wheels, 4 Tyres, 4 TPMS sensors, 4 Temp sensors,
  ESP32, OLED, LEDs, Buzzer, Enclosure, Battery, Brackets, Wire Harnesses).
- Interactive navigation: Rotate, Pan, Zoom, Camera Presets (RESET, TOP, FRONT, SIDE, ISOMETRIC).
- Exploded View Mode with dynamic component separation & 3D engineering labels.
- Live 3D Sensor Status Highlighting (SAFE=Dark rubber, WARNING=Yellow glow, CRITICAL=Red glow).
- Animated 3D Data Flow particles (Tyre -> ESP32 -> Prediction Engine).
- Tyre Selection with comprehensive side diagnostic telemetry panel.
- Transparent enclosure toggle & component visibility controls.
"""

import os
import math
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QCheckBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ui.styles import (
    BG_CARD, BG_PANEL, BORDER_COLOR, COLOR_CYAN,
    get_status_color, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED
)


class Vehicle3DView(QWidget):
    """
    Dedicated embedded 3D vehicle CAD page.
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.cad_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cad")

        # State flags
        self.is_exploded = False
        self.is_transparent_enclosure = True
        self.selected_tyre = "RL"
        self.data_flow_step = 0
        self.latest_snapshot = None

        # Data flow particle positions
        self.particle_phase = 0.0

        # Component actors registry
        self.actors = {}
        self.original_meshes = {}
        self.label_actors = []

        # Build UI layout
        self._init_ui()

        # Build 3D Scene
        self._build_3d_scene()

        # Animation timer for moving data particles (30 FPS)
        self.anim_timer = QTimer(self)
        self.anim_timer.timeout.connect(self._animate_data_flow)
        self.anim_timer.start(40)

    def _init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(16, 12, 16, 12)
        main_layout.setSpacing(14)

        # Left Column: 3D CAD Viewport & Camera Toolbar
        viewport_container = QFrame()
        viewport_container.setStyleSheet(f"""
            QFrame {{
                background-color: #0b0f14;
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
            }}
        """)
        vp_layout = QVBoxLayout(viewport_container)
        vp_layout.setContentsMargins(8, 8, 8, 8)
        vp_layout.setSpacing(8)

        # Top 3D Control Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        lbl_3d_title = QLabel("<b>3D CAD VEHICLE PROTOTYPE</b>")
        lbl_3d_title.setStyleSheet(f"color: {COLOR_CYAN}; font-size: 13px; letter-spacing: 1px;")
        toolbar.addWidget(lbl_3d_title)
        toolbar.addStretch()

        # Camera View Buttons
        self.btn_reset = QPushButton("RESET VIEW")
        self.btn_reset.setProperty("class", "SecondaryBtn")
        self.btn_reset.clicked.connect(self.view_isometric)

        self.btn_top = QPushButton("TOP VIEW")
        self.btn_top.setProperty("class", "SecondaryBtn")
        self.btn_top.clicked.connect(self.view_top)

        self.btn_front = QPushButton("FRONT VIEW")
        self.btn_front.setProperty("class", "SecondaryBtn")
        self.btn_front.clicked.connect(self.view_front)

        self.btn_side = QPushButton("SIDE VIEW")
        self.btn_side.setProperty("class", "SecondaryBtn")
        self.btn_side.clicked.connect(self.view_side)

        self.btn_exploded = QPushButton("💥 EXPLODED VIEW")
        self.btn_exploded.setProperty("class", "PrimaryBtn")
        self.btn_exploded.clicked.connect(self.toggle_exploded_view)

        toolbar.addWidget(self.btn_reset)
        toolbar.addWidget(self.btn_top)
        toolbar.addWidget(self.btn_front)
        toolbar.addWidget(self.btn_side)
        toolbar.addWidget(self.btn_exploded)

        vp_layout.addLayout(toolbar)

        # Embed PyVistaQt Interactor Widget
        self.plotter = QtInteractor(viewport_container)
        self.plotter.set_background("#0a0e14", top="#141a24")  # Engineering dark gradient
        self.plotter.enable_anti_aliasing()
        self.plotter.show_axes()
        vp_layout.addWidget(self.plotter.interactor, 1)

        # Bottom 3D status summary bar
        bot_bar = QHBoxLayout()
        self.lbl_data_flow_status = QLabel("DATA FLOW: TPMS Sensors ➜ Temperature Probes ➜ ESP32 ➜ Prediction Engine")
        self.lbl_data_flow_status.setStyleSheet(f"font-size: 11px; color: {TEXT_MUTED};")
        bot_bar.addWidget(self.lbl_data_flow_status)
        bot_bar.addStretch()

        self.chk_enclosure = QCheckBox("Transparent Enclosure")
        self.chk_enclosure.setChecked(True)
        self.chk_enclosure.stateChanged.connect(self._toggle_enclosure_transparency)
        bot_bar.addWidget(self.chk_enclosure)

        vp_layout.addLayout(bot_bar)
        main_layout.addWidget(viewport_container, 7)

        # Right Column: Side Diagnostic Telemetry & Inspection Panel
        side_panel = QFrame()
        side_panel.setFixedWidth(340)
        side_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_CARD};
                border: 1px solid {BORDER_COLOR};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        side_layout = QVBoxLayout(side_panel)
        side_layout.setSpacing(12)

        lbl_inspect_title = QLabel("COMPONENT INSPECTOR")
        lbl_inspect_title.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {COLOR_CYAN};")
        side_layout.addWidget(lbl_inspect_title)

        # Tyre Selector Combo
        sel_box = QHBoxLayout()
        sel_box.addWidget(QLabel("Select Tyre:"))
        self.combo_tyre_select = QComboBox()
        self.combo_tyre_select.addItems(["RL (Rear Left)", "FL (Front Left)", "FR (Front Right)", "RR (Rear Right)"])
        self.combo_tyre_select.currentIndexChanged.connect(self._on_tyre_combo_changed)
        sel_box.addWidget(self.combo_tyre_select, 1)
        side_layout.addLayout(sel_box)

        # Selected Tyre Diagnostic Box
        self.diag_box = QFrame()
        self.diag_box.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 2px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 12px;
            }}
        """)
        diag_layout = QVBoxLayout(self.diag_box)
        diag_layout.setSpacing(8)

        self.lbl_sel_tyre_header = QLabel("TYRE: REAR LEFT (RL)")
        self.lbl_sel_tyre_header.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")

        self.lbl_sel_status_badge = QLabel("SAFE")
        self.lbl_sel_status_badge.setStyleSheet("""
            background-color: rgba(46, 160, 67, 0.2);
            color: #3fb950;
            border: 1px solid #2ea043;
            border-radius: 4px;
            padding: 3px 8px;
            font-weight: bold;
            font-size: 11px;
        """)

        h_status = QHBoxLayout()
        h_status.addWidget(self.lbl_sel_tyre_header)
        h_status.addStretch()
        h_status.addWidget(self.lbl_sel_status_badge)
        diag_layout.addLayout(h_status)

        # Metrics rows
        self.lbl_sel_pressure = QLabel("Pressure: <b>32.0 PSI</b>")
        self.lbl_sel_temp = QLabel("Temperature: <b>33.2 °C</b>")
        self.lbl_sel_risk = QLabel("Risk: <b style='color:#3fb950;'>12%</b>")
        self.lbl_sel_rates = QLabel("Loss Rate: <b>-0.02 PSI/min</b>")
        self.lbl_sel_prediction = QLabel("Prediction: <b>Optimal pressure balance</b>")
        self.lbl_sel_prediction.setWordWrap(True)
        self.lbl_sel_action = QLabel("Action: <b>Continue normal driving</b>")
        self.lbl_sel_action.setWordWrap(True)

        for w in (self.lbl_sel_pressure, self.lbl_sel_temp, self.lbl_sel_risk,
                  self.lbl_sel_rates, self.lbl_sel_prediction, self.lbl_sel_action):
            diag_layout.addWidget(w)

        side_layout.addWidget(self.diag_box)

        # Component Hierarchy & Toggles
        grp_comp = QGroupBox("Model Components")
        grp_comp.setStyleSheet("font-weight: bold; color: #ffffff;")
        comp_layout = QVBoxLayout(grp_comp)

        self.chk_chassis = QCheckBox("Vehicle Chassis Frame")
        self.chk_chassis.setChecked(True)
        self.chk_chassis.toggled.connect(lambda v: self._toggle_actor_visibility("chassis", v))

        self.chk_wheels = QCheckBox("Wheels & Tyres (4x)")
        self.chk_wheels.setChecked(True)
        self.chk_wheels.toggled.connect(lambda v: self._toggle_group_visibility(["wheel", "tyre"], v))

        self.chk_sensors = QCheckBox("TPMS & Temp Sensors (4x)")
        self.chk_sensors.setChecked(True)
        self.chk_sensors.toggled.connect(lambda v: self._toggle_group_visibility(["tpms", "temp"], v))

        self.chk_esp32 = QCheckBox("ESP32 + Electronics Enclosure")
        self.chk_esp32.setChecked(True)
        self.chk_esp32.toggled.connect(lambda v: self._toggle_group_visibility(["esp32", "oled", "leds", "buzzer", "enclosure"], v))

        comp_layout.addWidget(self.chk_chassis)
        comp_layout.addWidget(self.chk_wheels)
        comp_layout.addWidget(self.chk_sensors)
        comp_layout.addWidget(self.chk_esp32)
        side_layout.addWidget(grp_comp)

        # 3D Data Flow Schematic representation
        flow_frame = QFrame()
        flow_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {BG_PANEL};
                border: 1px solid {BORDER_COLOR};
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        flow_layout = QVBoxLayout(flow_frame)
        flow_layout.setSpacing(4)

        flow_layout.addWidget(QLabel("<b>3D SENSOR PIPELINE FLOW</b>"))
        flow_text = QLabel(
            "TPMS SENSOR (Wheel Rim)\n"
            "   ↓ 433.92 MHz RF Packet\n"
            "Temperature Sensor (Hub)\n"
            "   ↓ 1-Wire Digital Bus\n"
            "ESP32 Control Unit (Enclosure)\n"
            "   ↓ Regression & Kalman Filter\n"
            "Prediction Engine\n"
            "   ↓ Risk Assessment (0-100%)\n"
            "PTMS Automotive Dashboard"
        )
        flow_text.setStyleSheet(f"font-family: Consolas, monospace; font-size: 10px; color: {COLOR_CYAN};")
        flow_layout.addWidget(flow_text)
        side_layout.addWidget(flow_frame)

        side_layout.addStretch()
        main_layout.addWidget(side_panel, 3)

    def _build_3d_scene(self):
        """Assembles all CAD components into the embedded PyVista plotter."""
        # 1. Vehicle Chassis
        chassis_mesh = pv.read(os.path.join(self.cad_dir, "chassis.stl"))
        self.original_meshes["chassis"] = chassis_mesh
        self.actors["chassis"] = self.plotter.add_mesh(
            chassis_mesh, color="#343d46", metallic=0.7, roughness=0.3, name="chassis"
        )

        # 2. Electronics Enclosure & Internal Modules
        enclosure_mesh = pv.read(os.path.join(self.cad_dir, "enclosure.stl")).translate((0, 0, 10))
        self.original_meshes["enclosure"] = enclosure_mesh
        self.actors["enclosure"] = self.plotter.add_mesh(
            enclosure_mesh, color="#58a6ff", opacity=0.35, roughness=0.1, name="enclosure"
        )

        esp32_mesh = pv.read(os.path.join(self.cad_dir, "esp32.stl")).translate((0, 0, 12))
        self.original_meshes["esp32"] = esp32_mesh
        self.actors["esp32"] = self.plotter.add_mesh(
            esp32_mesh, color="#1b4d3e", metallic=0.5, roughness=0.4, name="esp32"
        )

        oled_mesh = pv.read(os.path.join(self.cad_dir, "oled.stl")).translate((0, 0, 24))
        self.original_meshes["oled"] = oled_mesh
        self.actors["oled"] = self.plotter.add_mesh(
            oled_mesh, color="#0a0a0a", specular=1.0, roughness=0.1, name="oled"
        )

        leds_mesh = pv.read(os.path.join(self.cad_dir, "leds.stl")).translate((22, 0, 24))
        self.original_meshes["leds"] = leds_mesh
        self.actors["leds"] = self.plotter.add_mesh(
            leds_mesh, color="#2ea043", roughness=0.2, name="leds"
        )

        buzzer_mesh = pv.read(os.path.join(self.cad_dir, "buzzer.stl")).translate((-22, 0, 14))
        self.original_meshes["buzzer"] = buzzer_mesh
        self.actors["buzzer"] = self.plotter.add_mesh(
            buzzer_mesh, color="#21262d", roughness=0.5, name="buzzer"
        )

        # Brackets
        brackets_mesh = pv.read(os.path.join(self.cad_dir, "brackets.stl"))
        self.original_meshes["brackets"] = brackets_mesh
        self.actors["brackets"] = self.plotter.add_mesh(
            brackets_mesh, color="#484f58", metallic=0.6, roughness=0.4, name="brackets"
        )

        # 3. Four Wheel Packages: (FL, FR, RL, RR)
        # Positions: FL=(70, -56, 0), FR=(70, 56, 0), RL=(-70, -56, 0), RR=(-70, 56, 0)
        positions = {
            "FL": (70.0, -56.0, 0.0),
            "FR": (70.0, 56.0, 0.0),
            "RL": (-70.0, -56.0, 0.0),
            "RR": (-70.0, 56.0, 0.0)
        }

        base_wheel = pv.read(os.path.join(self.cad_dir, "wheel.stl"))
        base_tyre = pv.read(os.path.join(self.cad_dir, "tyre.stl"))
        base_tpms = pv.read(os.path.join(self.cad_dir, "tpms_sensor.stl"))
        base_temp = pv.read(os.path.join(self.cad_dir, "temperature_sensor.stl"))

        for tid, pos in positions.items():
            # Rim
            w_mesh = base_wheel.copy().translate(pos)
            self.original_meshes[f"wheel_{tid}"] = w_mesh
            self.actors[f"wheel_{tid}"] = self.plotter.add_mesh(
                w_mesh, color="#c9d1d9", metallic=0.8, roughness=0.2, name=f"wheel_{tid}"
            )

            # Tyre
            t_mesh = base_tyre.copy().translate(pos)
            self.original_meshes[f"tyre_{tid}"] = t_mesh
            self.actors[f"tyre_{tid}"] = self.plotter.add_mesh(
                t_mesh, color="#1c2128", roughness=0.8, name=f"tyre_{tid}"
            )

            # TPMS Sensor Assembly (mounted inside wheel rim at valve)
            tpms_pos = (pos[0], pos[1] + (2.0 if pos[1] > 0 else -2.0), pos[2] + 18.0)
            tpms_mesh = base_tpms.copy().translate(tpms_pos)
            self.original_meshes[f"tpms_{tid}"] = tpms_mesh
            self.actors[f"tpms_{tid}"] = self.plotter.add_mesh(
                tpms_mesh, color="#d29922", roughness=0.3, name=f"tpms_{tid}"
            )

            # Temperature Sensor Probe (mounted at wheel hub bearing)
            temp_pos = (pos[0], pos[1] + (-4.0 if pos[1] > 0 else 4.0), pos[2] - 5.0)
            temp_mesh = base_temp.copy().translate(temp_pos)
            self.original_meshes[f"temp_{tid}"] = temp_mesh
            self.actors[f"temp_{tid}"] = self.plotter.add_mesh(
                temp_mesh, color="#388bfd", metallic=0.9, roughness=0.2, name=f"temp_{tid}"
            )

            # Wire harness / signal conduit connecting wheel hub to chassis tray
            wire_pts = np.array([
                [pos[0], pos[1] * 0.7, 0.0],
                [pos[0] * 0.4, pos[1] * 0.4, 4.0],
                [0.0, 0.0, 8.0]
            ])
            spline = pv.Spline(wire_pts, 20)
            tube = spline.tube(radius=0.8)
            self.plotter.add_mesh(tube, color="#f0883e", roughness=0.5, name=f"wire_{tid}")

        # 4. Moving Data Flow Particles Mesh (Initial state)
        init_pts = np.array([[0.0, 0.0, 10.0], [10.0, 0.0, 10.0], [-10.0, 0.0, 10.0]], dtype=np.float32)
        self.flow_poly = pv.PolyData(init_pts)
        self.flow_actor = self.plotter.add_mesh(
            self.flow_poly, color="#58a6ff", point_size=12, render_points_as_spheres=True, name="data_flow"
        )

        # Initial camera
        self.view_isometric()

    def view_isometric(self):
        """Sets isometric perspective view."""
        self.plotter.camera_position = [(220, 240, 180), (0, 0, 5), (0, 0, 1)]
        self.plotter.reset_camera_clipping_range()
        self.plotter.render()

    def view_top(self):
        """Sets top-down perspective view."""
        self.plotter.camera_position = [(0, 0, 360), (0, 0, 0), (1, 0, 0)]
        self.plotter.reset_camera_clipping_range()
        self.plotter.render()

    def view_front(self):
        """Sets front perspective view."""
        self.plotter.camera_position = [(340, 0, 20), (0, 0, 0), (0, 0, 1)]
        self.plotter.reset_camera_clipping_range()
        self.plotter.render()

    def view_side(self):
        """Sets side perspective view."""
        self.plotter.camera_position = [(0, -340, 20), (0, 0, 0), (0, 0, 1)]
        self.plotter.reset_camera_clipping_range()
        self.plotter.render()

    def toggle_exploded_view(self):
        """Toggles between compact assembled vehicle and exploded inspection view."""
        self.is_exploded = not self.is_exploded
        self.btn_exploded.setText("COMPACT VIEW" if self.is_exploded else "💥 EXPLODED VIEW")

        # Clear any previous 3D labels
        self.plotter.remove_actor(self.label_actors)
        self.label_actors.clear()

        # Explosion offsets
        wheel_offsets = {
            "FL": (30.0, -45.0, 0.0),
            "FR": (30.0, 45.0, 0.0),
            "RL": (-30.0, -45.0, 0.0),
            "RR": (-30.0, 45.0, 0.0)
        }

        # Update meshes
        for key, orig_mesh in self.original_meshes.items():
            if self.is_exploded:
                if key == "chassis":
                    offset = (0, 0, -45.0)
                elif key == "enclosure":
                    offset = (0, 0, 45.0)
                elif key == "esp32":
                    offset = (0, 0, 18.0)
                elif key in ("oled", "leds"):
                    offset = (0, 0, 75.0)
                elif key == "buzzer":
                    offset = (0, 0, 35.0)
                elif "FL" in key:
                    offset = wheel_offsets["FL"]
                elif "FR" in key:
                    offset = wheel_offsets["FR"]
                elif "RL" in key:
                    offset = wheel_offsets["RL"]
                elif "RR" in key:
                    offset = wheel_offsets["RR"]
                else:
                    offset = (0, 0, 0)
                shifted = orig_mesh.copy().translate(offset)
            else:
                shifted = orig_mesh.copy()

            if key in self.actors:
                self.actors[key].mapper.dataset.copy_from(shifted)

        # If exploded, add 3D labels for engineering inspection
        if self.is_exploded:
            label_positions = [
                (70 + 30, -56 - 45, 25),   # TPMS-FL
                (70 + 30, 56 + 45, 25),    # TPMS-FR
                (-70 - 30, -56 - 45, 25),  # TPMS-RL
                (-70 - 30, 56 + 45, 25),   # TPMS-RR
                (0, 0, 24 + 75 + 5),       # OLED DISPLAY
                (0, 0, 12 + 18 + 5),       # ESP32 CONTROL UNIT
                (0, 0, 10 + 45 + 15),      # ELECTRONICS ENCLOSURE
                (-22, 0, 14 + 35 + 8),     # BUZZER
                (0, 0, -45 - 8)            # CHASSIS FRAME
            ]
            label_texts = [
                "TPMS-FL / TEMP-FL",
                "TPMS-FR / TEMP-FR",
                "TPMS-RL / TEMP-RL",
                "TPMS-RR / TEMP-RR",
                "OLED DISPLAY 128x64",
                "ESP32 CONTROL UNIT",
                "ELECTRONICS ENCLOSURE",
                "PIEZO BUZZER",
                "VEHICLE CHASSIS"
            ]
            lbl_pts = pv.PolyData(np.array(label_positions))
            lbl_actor = self.plotter.add_point_labels(
                lbl_pts, label_texts, font_size=10, text_color="white",
                point_color="#58a6ff", point_size=6, shape_color="#161b22", shape_opacity=0.8
            )
            self.label_actors.append(lbl_actor)

        self.plotter.render()

    def _toggle_enclosure_transparency(self, state: int):
        self.is_transparent_enclosure = bool(state)
        if "enclosure" in self.actors:
            self.actors["enclosure"].GetProperty().SetOpacity(0.35 if self.is_transparent_enclosure else 1.0)
            self.plotter.render()

    def _toggle_actor_visibility(self, name: str, visible: bool):
        if name in self.actors:
            self.actors[name].SetVisibility(visible)
            self.plotter.render()

    def _toggle_group_visibility(self, prefixes: list, visible: bool):
        for key, actor in self.actors.items():
            for p in prefixes:
                if key.startswith(p):
                    actor.SetVisibility(visible)
        self.plotter.render()

    def _on_tyre_combo_changed(self, idx: int):
        mapping = {0: "RL", 1: "FL", 2: "FR", 3: "RR"}
        self.selected_tyre = mapping.get(idx, "RL")
        self._highlight_selected_tyre()
        if self.latest_snapshot:
            self._update_side_panel(self.latest_snapshot)

    def _highlight_selected_tyre(self):
        """Highlights the selected tyre with outline / gold accent."""
        if not self.latest_snapshot:
            return

        tyres = self.latest_snapshot.get("tyres", {})
        for tid in ("FL", "FR", "RL", "RR"):
            tyre_actor = self.actors.get(f"tyre_{tid}")
            if not tyre_actor:
                continue

            status = tyres.get(tid, {}).get("status", "SAFE")
            if tid == self.selected_tyre:
                # Add wireframe or brighter highlight
                tyre_actor.GetProperty().SetEdgeVisibility(True)
                tyre_actor.GetProperty().SetEdgeColor(0.9, 0.8, 0.2)
                tyre_actor.GetProperty().SetLineWidth(2.5)
            else:
                tyre_actor.GetProperty().SetEdgeVisibility(False)

        self.plotter.render()

    def _animate_data_flow(self):
        """Advances moving data particles along paths between wheels and ESP32."""
        self.particle_phase = (self.particle_phase + 0.05) % 1.0

        wheel_origins = [
            np.array([70.0, -56.0, 0.0]),   # FL
            np.array([70.0, 56.0, 0.0]),    # FR
            np.array([-70.0, -56.0, 0.0]),  # RL
            np.array([-70.0, 56.0, 0.0])    # RR
        ]
        esp_center = np.array([0.0, 0.0, 14.0])

        current_points = []
        for origin in wheel_origins:
            # Interpolate 3 particles per route
            for frac in (0.0, 0.33, 0.66):
                t = (self.particle_phase + frac) % 1.0
                pt = (1.0 - t) * origin + t * esp_center
                # Add slight curve arc
                pt[2] += 8.0 * math.sin(t * math.pi)
                current_points.append(pt)

        # Update points in the polydata dataset
        pts_arr = np.array(current_points, dtype=np.float32)
        self.flow_poly.points = pts_arr
        self.plotter.render()

    def update_state(self, snapshot: dict):
        """
        Receives real-time Digital Twin state snapshot from simulation engine.
        Updates tyre colors, sensor glows, and side panel.
        """
        self.latest_snapshot = snapshot
        tyres = snapshot.get("tyres", {})

        # Status color mappings for 3D meshes
        # SAFE: dark charcoal grey rubber (0.12, 0.14, 0.16)
        # CAUTION: warm amber (0.85, 0.60, 0.10)
        # WARNING: orange (0.92, 0.45, 0.12)
        # CRITICAL: bright red (0.95, 0.15, 0.15)
        color_lut = {
            "SAFE": (0.12, 0.14, 0.16),
            "NORMAL": (0.14, 0.18, 0.20),
            "CAUTION": (0.85, 0.60, 0.10),
            "WARNING": (0.92, 0.45, 0.12),
            "CRITICAL": (0.95, 0.15, 0.15)
        }

        for tid in ("FL", "FR", "RL", "RR"):
            tyre_data = tyres.get(tid, {})
            status = tyre_data.get("status", "SAFE")
            rgb = color_lut.get(status, (0.12, 0.14, 0.16))

            # Update Tyre Actor Color
            tyre_actor = self.actors.get(f"tyre_{tid}")
            if tyre_actor:
                tyre_actor.GetProperty().SetColor(rgb)
                if status in ("WARNING", "CRITICAL"):
                    tyre_actor.GetProperty().SetDiffuse(0.9)
                    tyre_actor.GetProperty().SetAmbient(0.3)
                else:
                    tyre_actor.GetProperty().SetDiffuse(0.6)
                    tyre_actor.GetProperty().SetAmbient(0.1)

            # Update corresponding TPMS and Temp sensor components
            tpms_actor = self.actors.get(f"tpms_{tid}")
            temp_actor = self.actors.get(f"temp_{tid}")
            if status in ("WARNING", "CRITICAL"):
                if tpms_actor:
                    tpms_actor.GetProperty().SetColor(rgb)
                    tpms_actor.GetProperty().SetAmbient(0.5)
                if temp_actor:
                    temp_actor.GetProperty().SetColor(rgb)
                    temp_actor.GetProperty().SetAmbient(0.5)
            else:
                if tpms_actor:
                    tpms_actor.GetProperty().SetColor((0.82, 0.60, 0.13))
                    tpms_actor.GetProperty().SetAmbient(0.1)
                if temp_actor:
                    temp_actor.GetProperty().SetColor((0.22, 0.55, 0.98))
                    temp_actor.GetProperty().SetAmbient(0.1)

        # Update Side Information Panel
        self._update_side_panel(snapshot)
        self._highlight_selected_tyre()
        self.plotter.render()

    def _update_side_panel(self, snapshot: dict):
        """Updates right-hand diagnostic panel for currently selected tyre."""
        tyres = snapshot.get("tyres", {})
        data = tyres.get(self.selected_tyre, {})

        p_psi = data.get("pressure_psi", 32.0)
        t_c = data.get("temperature_c", 33.0)
        risk = data.get("risk_score", 10.0)
        status = data.get("status", "SAFE")
        dp_dt = data.get("pressure_rate_min", 0.0)
        prediction = data.get("prediction", "Optimal parameters")
        recommendation = data.get("recommendation", "Continue normal driving.")

        color = get_status_color(status)

        name_map = {"RL": "REAR LEFT (RL)", "FL": "FRONT LEFT (FL)", "FR": "FRONT RIGHT (FR)", "RR": "REAR RIGHT (RR)"}
        self.lbl_sel_tyre_header.setText(f"TYRE: {name_map.get(self.selected_tyre, self.selected_tyre)}")

        self.lbl_sel_status_badge.setText(status)
        self.lbl_sel_status_badge.setStyleSheet(f"""
            background-color: rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.25);
            color: {color};
            border: 1px solid {color};
            border-radius: 4px;
            padding: 3px 8px;
            font-weight: bold;
            font-size: 11px;
        """)

        self.lbl_sel_pressure.setText(f"Pressure: <b>{p_psi:.1f} PSI</b> ({p_psi * 0.0689:.2f} bar)")
        self.lbl_sel_temp.setText(f"Temperature: <b>{t_c:.1f} °C</b> ({t_c * 9/5 + 32:.1f} °F)")
        self.lbl_sel_risk.setText(f"Risk: <b style='color:{color};'>{risk:.0f}%</b>")
        self.lbl_sel_rates.setText(f"Pressure Loss Rate: <b>{dp_dt:+.2f} PSI/min</b>")
        self.lbl_sel_prediction.setText(f"Prediction: <b>{prediction}</b>")
        self.lbl_sel_action.setText(f"Recommendation: <b>{recommendation}</b>")

        if status in ("WARNING", "CRITICAL"):
            self.diag_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_PANEL};
                    border: 2px solid {color};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
        else:
            self.diag_box.setStyleSheet(f"""
                QFrame {{
                    background-color: {BG_PANEL};
                    border: 2px solid {BORDER_COLOR};
                    border-radius: 8px;
                    padding: 12px;
                }}
            """)
