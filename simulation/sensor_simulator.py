"""
Predictive Tyre Monitoring System (PTMS) - Sensor Simulator Coordinator
Coordinates the 4 wheel packages (FL, FR, RL, RR) combining tyre physics,
direct TPMS transmitters, and temperature sensors.
"""

from typing import Dict, Any, List
import sys
import os

# Support relative and absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulation.tyre_model import TyreModel
from sensors.tpms import TPMSSensor
from sensors.temperature import TemperatureSensor


class SensorSimulator:
    """
    Simulates the 4 physical wheel nodes equipped with TPMS pressure sensors
    and temperature sensors.
    """

    TYRE_IDS = ["FL", "FR", "RL", "RR"]

    def __init__(self, nominal_pressure: float = 32.0, ambient_temp: float = 28.0):
        self.tyres: Dict[str, TyreModel] = {}
        self.tpms_sensors: Dict[str, TPMSSensor] = {}
        self.temp_sensors: Dict[str, TemperatureSensor] = {}

        for tid in self.TYRE_IDS:
            self.tyres[tid] = TyreModel(tid, nominal_pressure, ambient_temp)
            self.tpms_sensors[tid] = TPMSSensor(tid, baseline_pressure_psi=nominal_pressure)
            self.temp_sensors[tid] = TemperatureSensor(tid, baseline_temp_c=ambient_temp + 5.0)

    def set_fault(self, tyre_id: str, fault_mode: str, severity: float = 0.5):
        """Injects a fault into a specific tyre."""
        if tyre_id in self.tyres:
            self.tyres[tyre_id].set_fault(fault_mode, severity)

    def reset_all(self):
        """Resets all tyres to nominal operating condition."""
        for tyre in self.tyres.values():
            tyre.reset_to_nominal()

    def update_physics(self, dt: float, speed_multiplier: float = 1.0):
        """Advances physical state of all tyres."""
        for tyre in self.tyres.values():
            tyre.update(dt, speed_multiplier)

    def sample_all_sensors(self, add_noise: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Samples all 4 TPMS and temperature sensors to generate telemetry frames.
        """
        readings: Dict[str, Dict[str, Any]] = {}
        for tid in self.TYRE_IDS:
            tyre = self.tyres[tid]
            tpms_packet = self.tpms_sensors[tid].read_pressure_packet(tyre.pressure_psi, add_noise)
            temp_packet = self.temp_sensors[tid].read_temperature_packet(tyre.temperature_c, add_noise)

            readings[tid] = {
                "tyre_id": tid,
                "pressure_psi": tpms_packet["pressure_psi"],
                "pressure_bar": tpms_packet["pressure_bar"],
                "pressure_kpa": tpms_packet["pressure_kpa"],
                "temperature_c": temp_packet["temp_c"],
                "temperature_f": temp_packet["temp_f"],
                "pressure_rate": tyre.pressure_rate,
                "temp_rate": tyre.temp_rate,
                "tpms_sensor_id": tpms_packet["sensor_id"],
                "temp_sensor_id": temp_packet["sensor_id"],
                "battery_voltage": tpms_packet["battery_voltage"],
                "battery_health_pct": tpms_packet["battery_health_pct"],
                "rssi_dbm": tpms_packet["rssi_dbm"],
                "fault_mode": tyre.fault_mode,
                "severity": tyre.severity
            }
        return readings
