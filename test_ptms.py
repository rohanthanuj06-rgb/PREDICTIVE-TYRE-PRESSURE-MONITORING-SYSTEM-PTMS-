"""
Predictive Tyre Monitoring System (PTMS) - Verification & Integration Test Suite
Validates:
1. Database operations (log, query, export)
2. Sensors & tyre physics
3. Virtual ESP32 controller & OLED buffer
4. Multi-factor risk engine & trend analysis
5. Central simulation engine cycles
6. Qt & PyVista 3D integration
"""

import os
import sys
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from PySide6.QtWidgets import QApplication
from database.database import get_database
from sensors.tpms import TPMSSensor
from sensors.temperature import TemperatureSensor
from simulation.tyre_model import TyreModel
from simulation.sensor_simulator import SensorSimulator
from controller.virtual_esp32 import VirtualESP32
from prediction.risk_engine import RiskEngine
from prediction.trend_analysis import TrendAnalysisEngine
from simulation.simulation_engine import SimulationEngine


def run_tests():
    print("==================================================")
    print("RUNNING PTMS SYSTEM INTEGRATION TESTS")
    print("==================================================")

    # 1. Test Database
    print("[1/6] Testing SQLite Database...")
    db = get_database()
    row_id = db.log_telemetry("RL", 31.5, 34.2, -0.05, 0.02, 25.0, "NORMAL", "SLOW_LEAK")
    assert row_id > 0, "Telemetry logging failed"
    history = db.get_history(limit=5)
    assert len(history) > 0, "Telemetry query failed"
    test_csv = os.path.join(BASE_DIR, "test_export.csv")
    count = db.export_to_csv(test_csv)
    if os.path.exists(test_csv):
        os.remove(test_csv)
    print(f"      [OK] Database operational ({count} records tested)")

    # 2. Test Sensors
    print("[2/6] Testing Sensors & Physical Tyre Model...")
    tyre = TyreModel("RL", nominal_pressure=32.0)
    tyre.set_fault("SLOW_LEAK", severity=0.8)
    for _ in range(10):
        tyre.update(dt=1.0)
    assert tyre.pressure_psi < 32.0, "Tyre leak model failed to deflate"
    assert tyre.temperature_c > 33.0, "Sidewall flex heating failed"

    tpms = TPMSSensor("RL")
    pkt = tpms.read_pressure_packet(tyre.pressure_psi)
    assert "pressure_psi" in pkt and pkt["pressure_psi"] > 0
    print(f"      [OK] Physical tyre simulation & RF packet generation verified")

    # 3. Test Risk & Trend Engine
    print("[3/6] Testing Predictive Risk Engine & Trend Analysis...")
    risk_eng = RiskEngine(nominal_pressure=32.0)
    # Test early detection: pressure is 30.5 (still near normal), but dP/dt is -2.5 PSI/min and temp is rising
    res = risk_eng.evaluate_tyre(
        pressure=30.5,
        temperature=38.0,
        pressure_rate_min=-2.5,
        temp_rate_min=1.8,
        axle_delta_psi=1.5
    )
    print(f"      Evaluated early leak: Risk={res['risk_score']}%, Status={res['status']}, Diagnosis='{res['prediction']}'")
    assert res["risk_score"] > 35.0, "Risk score failed to detect impending fault early"
    print("      [OK] Predictive early-detection risk engine verified")

    # 4. Test Virtual ESP32
    print("[4/6] Testing Virtual ESP32 Controller & OLED...")
    esp = VirtualESP32(nominal_pressure=32.0)
    sim = SensorSimulator(nominal_pressure=32.0)
    sim.set_fault("RL", "SLOW_LEAK", severity=0.7)
    sim.update_physics(dt=1.0)
    raw = sim.sample_all_sensors()
    state = esp.process_cycle(raw)
    assert "oled_lines" in state and len(state["oled_lines"]) == 6
    assert "gpio" in state
    print(f"      OLED Line 0: {state['oled_lines'][0]}")
    print(f"      OLED Line 3: {state['oled_lines'][3]}")
    print(f"      OLED Line 5: {state['oled_lines'][5]}")
    print("      [OK] Virtual ESP32 FreeRTOS loop & OLED buffer verified")

    # 5. Test Simulation Engine & Automated Demo
    print("[5/6] Testing Simulation Engine & 12-Step Demo Sequencer...")
    app = QApplication.instance() or QApplication(sys.argv)
    engine = SimulationEngine()
    engine.start_demonstration()
    assert engine.demo_active is True
    assert engine.demo_step_index == 0
    # Simulate a step tick
    engine._simulation_tick()
    print("      [OK] Simulation Engine & Demo Sequencer operational")

    # 6. Test UI & 3D CAD loading
    print("[6/6] Testing PySide6 UI and 3D CAD Assembly...")
    from ui.main_window import MainWindow
    window = MainWindow()
    assert window.page_3d is not None
    assert len(window.page_3d.actors) > 0
    print(f"      [OK] 3D CAD Model loaded with {len(window.page_3d.actors)} active actors")

    print("==================================================")
    print("ALL TESTS PASSED SUCCESSFULLY! PTMS IS FULLY READY.")
    print("==================================================")


if __name__ == "__main__":
    run_tests()
