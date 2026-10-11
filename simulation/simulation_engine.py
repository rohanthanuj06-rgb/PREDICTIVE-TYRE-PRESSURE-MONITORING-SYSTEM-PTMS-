"""
Predictive Tyre Monitoring System (PTMS) - Central Simulation Engine
The Single Source of Truth for the entire Digital Twin architecture.
Coordinates:
- SensorSimulator (Wheel physics & Transducers)
- VirtualESP32 (Edge diagnostics, FreeRTOS tasks, GPIO, OLED)
- PTMSDatabase (Persistent telemetry logging)
- 12-Step Automated Demonstration Sequencer
"""

import time
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, QTimer, Signal

from simulation.sensor_simulator import SensorSimulator
from controller.virtual_esp32 import VirtualESP32
from database.database import get_database


class SimulationEngine(QObject):
    """
    Central simulation engine emitting real-time signals to all UI pages.
    """

    # Signals
    data_updated = Signal(dict)
    alert_triggered = Signal(str, str, str)  # tyre_id, severity, message
    demo_step_changed = Signal(int, str, str)  # step_num (1-12), title, desc

    DEMO_STEPS = [
        (1, "All Tyres SAFE", "All 4 wheels running at nominal 32.0 PSI and 33°C. System status SAFE, Green LED ON."),
        (2, "Fault Injected: RL Slow Leak", "Micro-leakage initiated on Rear Left (RL) tyre valve stem. Bead sealing begins degrading."),
        (3, "Gradual Pressure Decrease", "RL pressure declining slowly (~0.12 PSI/s). Standard TPMS would remain silent, but PTMS tracks derivative."),
        (4, "Temperature Begins Rising", "Under-inflation causes increased sidewall deflection and hysteretic internal friction heat."),
        (5, "Trend Analysis Detects Anomaly", "Linear regression detects dP/dt < -1.5 PSI/min and dT/dt > +1.2°C/min simultaneously."),
        (6, "Predictive Risk Score Escalating", "Multi-factor risk engine increases RL Risk Score from 15% -> 42% (Entering CAUTION)."),
        (7, "Status Transition: SAFE -> CAUTION -> WARNING", "Predictive threshold breached prior to physical deflation danger limit."),
        (8, "3D CAD Model Visual Warning", "3D vehicle highlights RL tyre in Warning Amber/Yellow with pulsing sensor packet particles."),
        (9, "Virtual OLED Screen Synchronized", "ESP32 updates SSD1306 128x64 display buffer with live warning line and degraded telemetry."),
        (10, "Hardware Peripherals State Update", "GPIO 18 (Green) turns OFF, GPIO 19 (Yellow) illuminates. Inspection flag set."),
        (11, "Critical Escalation & Buzzer", "Pressure reaches critical threshold. GPIO 21 (Red) activates, 2.7 kHz Piezo buzzer pulses."),
        (12, "Final Predictive Recommendation", "System issues urgent: 'PREDICTED TYRE FAILURE RISK' - 'INSPECTION RECOMMENDED'.")
    ]

    def __init__(self, parent=None):
        super().__init__(parent)

        self.sensor_sim = SensorSimulator(nominal_pressure=32.0, ambient_temp=28.0)
        self.esp32 = VirtualESP32(nominal_pressure=32.0)
        self.db = get_database()

        # Engine parameters
        self.speed_multiplier = 1.0
        self.target_tyre = "RL"
        self.current_fault_mode = "NORMAL"
        self.current_severity = 0.5
        self.is_running = True

        # Demo Mode state
        self.demo_active = False
        self.demo_step_index = 0
        self.demo_step_timer = 0.0
        self.demo_step_durations = [6.0, 5.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 7.0, 8.0]

        # Telemetry logging decimation (e.g. log to DB every 1.0 s)
        self.last_db_log_time = 0.0
        self.last_alert_logged = None

        # Main simulation timer (100 ms = 10 Hz)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._simulation_tick)
        self.last_tick_time = time.time()

    def start(self):
        """Starts the simulation loop."""
        self.is_running = True
        self.last_tick_time = time.time()
        self.timer.start(100)

    def pause(self):
        """Pauses simulation."""
        self.is_running = False
        self.timer.stop()

    def set_speed(self, speed: float):
        """Sets simulation speed multiplier (0.5x, 1x, 2x, 5x)."""
        self.speed_multiplier = max(0.1, min(10.0, speed))

    def set_fault(self, tyre_id: str, fault_mode: str, severity: float = 0.5):
        """Manually sets a tyre fault mode."""
        self.target_tyre = tyre_id
        self.current_fault_mode = fault_mode
        self.current_severity = severity
        self.sensor_sim.set_fault(tyre_id, fault_mode, severity)

    def reset_all_tyres(self):
        """Resets all tyres and controller to nominal safe state."""
        self.demo_active = False
        self.current_fault_mode = "NORMAL"
        self.sensor_sim.reset_all()

    def start_demonstration(self):
        """Launches the automatic 12-step demonstration scenario."""
        self.reset_all_tyres()
        self.demo_active = True
        self.demo_step_index = 0
        self.demo_step_timer = 0.0
        step_num, title, desc = self.DEMO_STEPS[0]
        self.demo_step_changed.emit(step_num, title, desc)

    def stop_demonstration(self):
        """Halts the automated demonstration."""
        self.demo_active = False

    def _simulation_tick(self):
        """Core high-frequency tick executed every 100ms."""
        now = time.time()
        dt = now - self.last_tick_time
        if dt <= 0:
            dt = 0.1
        self.last_tick_time = now

        # 1. Advance Demo Sequence if active
        if self.demo_active:
            self._handle_demo_tick(dt)

        # 2. Update physical model
        self.sensor_sim.update_physics(dt, self.speed_multiplier)

        # 3. Read sensor packets
        raw_readings = self.sensor_sim.sample_all_sensors(add_noise=True)

        # 4. Pass to Virtual ESP32
        esp32_state = self.esp32.process_cycle(raw_readings)

        # 5. Check and emit alerts
        active_alert = esp32_state["active_alert"]
        if active_alert and active_alert != self.last_alert_logged:
            self.last_alert_logged = active_alert
            worst_tyre = self.target_tyre
            for tid, tdata in esp32_state["tyres"].items():
                if tdata["status"] in ("WARNING", "CRITICAL"):
                    worst_tyre = tid
                    break
            self.db.log_alert(worst_tyre, esp32_state["overall_status"], active_alert)
            self.alert_triggered.emit(worst_tyre, esp32_state["overall_status"], active_alert)

        # 6. Periodic DB Logging (every 1 second)
        if now - self.last_db_log_time >= 1.0:
            self.last_db_log_time = now
            batch = []
            for tid, tdata in esp32_state["tyres"].items():
                batch.append({
                    "tyre_id": tid,
                    "pressure": tdata["pressure_psi"],
                    "temperature": tdata["temperature_c"],
                    "pressure_rate": tdata["pressure_rate_min"],
                    "temp_rate": tdata["temp_rate_min"],
                    "risk_score": tdata["risk_score"],
                    "status": tdata["status"],
                    "fault_type": tdata.get("fault_mode", "NORMAL")
                })
            self.db.log_telemetry_batch(batch)

        # 7. Package complete digital twin snapshot and emit
        snapshot = {
            **esp32_state,
            "timestamp": now,
            "speed_multiplier": self.speed_multiplier,
            "demo_state": {
                "active": self.demo_active,
                "step_index": self.demo_step_index + 1,
                "total_steps": len(self.DEMO_STEPS),
                "step_title": self.DEMO_STEPS[self.demo_step_index][1] if self.demo_active else "Manual Simulation",
                "step_desc": self.DEMO_STEPS[self.demo_step_index][2] if self.demo_active else "System under user manual control.",
                "step_progress": min(1.0, self.demo_step_timer / max(1.0, self.demo_step_durations[self.demo_step_index])) if self.demo_active else 0.0
            }
        }

        self.data_updated.emit(snapshot)

    def _handle_demo_tick(self, dt: float):
        """Advances the 12-step demonstration logic."""
        self.demo_step_timer += dt * self.speed_multiplier
        cur_duration = self.demo_step_durations[self.demo_step_index]

        # Step actions executed at entry of step
        step_idx = self.demo_step_index

        if step_idx == 0:  # Step 1: SAFE
            pass
        elif step_idx == 1:  # Step 2: Incur RL slow leak
            self.sensor_sim.set_fault("RL", "SLOW_LEAK", severity=0.35)
        elif step_idx == 2:  # Step 3: Leak accelerates slightly
            self.sensor_sim.set_fault("RL", "SLOW_LEAK", severity=0.55)
        elif step_idx == 3:  # Step 4: Temperature rises due to flexing
            self.sensor_sim.set_fault("RL", "SLOW_LEAK", severity=0.7)
        elif step_idx == 6:  # Step 7: Warning
            self.sensor_sim.set_fault("RL", "SLOW_LEAK", severity=0.85)
        elif step_idx == 10: # Step 11: Critical
            self.sensor_sim.set_fault("RL", "RAPID_LEAK", severity=0.95)

        # Step transition
        if self.demo_step_timer >= cur_duration:
            self.demo_step_timer = 0.0
            self.demo_step_index += 1
            if self.demo_step_index >= len(self.DEMO_STEPS):
                # Demo completed
                self.demo_active = False
                self.demo_step_index = len(self.DEMO_STEPS) - 1
            else:
                step_num, title, desc = self.DEMO_STEPS[self.demo_step_index]
                self.demo_step_changed.emit(step_num, title, desc)
