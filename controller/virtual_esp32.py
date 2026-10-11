"""
Predictive Tyre Monitoring System (PTMS) - Virtual ESP32 Controller
Simulates physical ESP32 micro-controller running embedded firmware:
- Dual-core FreeRTOS task abstraction:
  - Core 0: Sensor RF packet receiver & 1-Wire temperature acquisition
  - Core 1: Edge predictive trend evaluation, OLED rendering buffer, GPIO control
- Virtual Hardware Peripherals:
  - Monochrome 128x64 I2C SSD1306 OLED Display Framebuffer
  - GPIO 18: Green LED (System Normal / Safe)
  - GPIO 19: Yellow LED (Caution / Warning)
  - GPIO 21: Red LED (Critical Hazard Alert)
  - GPIO 22: PWM Active Piezo Buzzer (2.7 kHz resonant tone)
- UART Serial Telemetry Streamer
"""

import time
from typing import Dict, Any, List, Optional
from prediction.risk_engine import RiskEngine
from prediction.trend_analysis import TrendAnalysisEngine


class VirtualOLED:
    """
    Simulates a 128x64 SSD1306 I2C OLED display with text rendering lines.
    """

    def __init__(self):
        self.width = 128
        self.height = 64
        self.lines: List[str] = [
            "    PTMS v2.4    ",
            "FL 32.0P  33C [OK]",
            "FR 32.0P  33C [OK]",
            "RL 32.0P  33C [OK]",
            "RR 32.0P  33C [OK]",
            "STATUS: SAFE     "
        ]
        self.contrast = 255
        self.is_powered = True
        self.inverted = False

    def update_display(self, tyre_data: Dict[str, Dict[str, Any]], overall_status: str, alert_text: str = ""):
        """Renders automotive telemetry into OLED textual screen buffer."""
        fl = tyre_data.get("FL", {"pressure_psi": 32.0, "temperature_c": 32.0})
        fr = tyre_data.get("FR", {"pressure_psi": 32.0, "temperature_c": 32.0})
        rl = tyre_data.get("RL", {"pressure_psi": 32.0, "temperature_c": 32.0})
        rr = tyre_data.get("RR", {"pressure_psi": 32.0, "temperature_c": 32.0})

        line0 = "=== PTMS AUTO ==="
        line1 = f"FL {fl['pressure_psi']:4.1f}P {int(fl['temperature_c']):2d}C"
        line2 = f"FR {fr['pressure_psi']:4.1f}P {int(fr['temperature_c']):2d}C"
        line3 = f"RL {rl['pressure_psi']:4.1f}P {int(rl['temperature_c']):2d}C"
        line4 = f"RR {rr['pressure_psi']:4.1f}P {int(rr['temperature_c']):2d}C"

        if alert_text:
            line5 = alert_text[:17]
        else:
            line5 = f"STATE: {overall_status:<10}"

        self.lines = [line0, line1, line2, line3, line4, line5]

    def get_text(self) -> str:
        return "\n".join(self.lines)


class VirtualESP32:
    """
    Virtual ESP32 Microcontroller Unit.
    Coordinates edge sensing, peripheral control, OLED display, and edge diagnostics.
    """

    def __init__(self, nominal_pressure: float = 32.0):
        self.firmware_version = "PTMS-ESP32-v2.4.1"
        self.nominal_pressure = nominal_pressure
        self.cpu_freq_mhz = 240
        self.heap_free_bytes = 214580
        self.wifi_connected = True
        self.ip_address = "192.168.4.1"  # Virtual AP/STA

        # Submodules
        self.trend_engine = TrendAnalysisEngine(window_size=35)
        self.risk_engine = RiskEngine(nominal_pressure=nominal_pressure)
        self.oled = VirtualOLED()

        # Peripheral states
        self.led_green = True     # GPIO 18
        self.led_yellow = False   # GPIO 19
        self.led_red = False      # GPIO 21
        self.buzzer_active = False # GPIO 22
        self.buzzer_frequency_hz = 0

        # Diagnostics & Alert tracking
        self.active_alert: Optional[str] = None
        self.overall_status = "SAFE"
        self.overall_health_pct = 98.0
        self.highest_risk = 0.0
        self.processed_packet_count = 0
        self.last_cycle_time = time.time()

        # Evaluated cache
        self.latest_evaluations: Dict[str, Dict[str, Any]] = {}

    def process_cycle(self, sensor_readings: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Executes one full FreeRTOS control loop cycle:
        1. Ingest raw sensor packets
        2. Perform edge trend linear regression
        3. Evaluate predictive risk score for each wheel
        4. Manage GPIO pins (LEDs and Buzzer)
        5. Update Virtual OLED buffer
        6. Return master controller state frame
        """
        now = time.time()
        self.processed_packet_count += 1
        self.last_cycle_time = now

        # 1. Update temporal trend analysis
        self.trend_engine.update(now, sensor_readings)
        current_pressures = {tid: d["pressure_psi"] for tid, d in sensor_readings.items()}
        trend_stats = self.trend_engine.analyze_trends(current_pressures)

        # 2. Evaluate risk for all 4 tyres
        evaluations: Dict[str, Dict[str, Any]] = {}
        max_risk = 0.0
        worst_status = "SAFE"
        primary_alert = None

        status_ranks = {"SAFE": 0, "NORMAL": 1, "CAUTION": 2, "WARNING": 3, "CRITICAL": 4}

        for tid, s_data in sensor_readings.items():
            t_stat = trend_stats.get(tid, {
                "pressure_rate_psi_min": 0.0,
                "temp_rate_c_min": 0.0,
                "axle_delta_psi": 0.0
            })

            eval_res = self.risk_engine.evaluate_tyre(
                pressure=s_data["pressure_psi"],
                temperature=s_data["temperature_c"],
                pressure_rate_min=t_stat["pressure_rate_psi_min"],
                temp_rate_min=t_stat["temp_rate_c_min"],
                axle_delta_psi=t_stat["axle_delta_psi"]
            )

            # Combine sensor + evaluation data
            evaluations[tid] = {
                **s_data,
                "pressure_rate_min": t_stat["pressure_rate_psi_min"],
                "temp_rate_min": t_stat["temp_rate_c_min"],
                "axle_delta_psi": t_stat["axle_delta_psi"],
                "risk_score": eval_res["risk_score"],
                "status": eval_res["status"],
                "prediction": eval_res["prediction"],
                "recommendation": eval_res["recommendation"],
                "diagnostics": eval_res["diagnostics"],
                "health_pct": round(max(0.0, 100.0 - eval_res["risk_score"]), 1)
            }

            if eval_res["risk_score"] > max_risk:
                max_risk = eval_res["risk_score"]

            if status_ranks[eval_res["status"]] > status_ranks[worst_status]:
                worst_status = eval_res["status"]
                if eval_res["status"] in ("CAUTION", "WARNING", "CRITICAL"):
                    primary_alert = f"{tid}: {eval_res['prediction'].upper()}"

        self.latest_evaluations = evaluations
        self.highest_risk = max_risk
        self.overall_status = worst_status
        self.overall_health_pct = round(max(0.0, 100.0 - max_risk), 1)
        self.active_alert = primary_alert

        # 3. Update Hardware GPIO & Peripherals
        if worst_status in ("SAFE", "NORMAL"):
            self.led_green = True
            self.led_yellow = False
            self.led_red = False
            self.buzzer_active = False
            self.buzzer_frequency_hz = 0
        elif worst_status == "CAUTION":
            self.led_green = False
            self.led_yellow = True
            self.led_red = False
            self.buzzer_active = False
            self.buzzer_frequency_hz = 0
        elif worst_status == "WARNING":
            self.led_green = False
            self.led_yellow = True
            self.led_red = False
            self.buzzer_active = False
            self.buzzer_frequency_hz = 0
        else:  # CRITICAL
            self.led_green = False
            self.led_yellow = False
            self.led_red = True
            self.buzzer_active = True
            self.buzzer_frequency_hz = 2700  # Resonant piercing frequency

        # 4. Update OLED Display
        alert_summary = primary_alert if primary_alert else f"STATE: {worst_status}"
        self.oled.update_display(evaluations, worst_status, alert_summary)

        return {
            "tyres": evaluations,
            "overall_status": self.overall_status,
            "overall_health_pct": self.overall_health_pct,
            "highest_risk": self.highest_risk,
            "active_alert": self.active_alert,
            "gpio": {
                "led_green": self.led_green,
                "led_yellow": self.led_yellow,
                "led_red": self.led_red,
                "buzzer_active": self.buzzer_active,
                "buzzer_freq_hz": self.buzzer_frequency_hz
            },
            "oled_lines": self.oled.lines,
            "esp32_metrics": {
                "firmware": self.firmware_version,
                "cpu_freq_mhz": self.cpu_freq_mhz,
                "heap_free": self.heap_free_bytes,
                "packet_count": self.processed_packet_count,
                "cycle_hz": 10.0
            }
        }
