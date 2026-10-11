"""
Predictive Tyre Monitoring System (PTMS) - TPMS Sensor Module
Simulates physical direct TPMS wheel-mounted sensor assembly.
Features:
- Piezo-resistive micro-electromechanical pressure transducer
- 12-bit ADC quantization
- 433.92 MHz RF transmission packet encoding
- Battery voltage (CR2032 coin cell)
- Signal strength (RSSI dBm)
"""

import random
import time
from typing import Dict, Any


class TPMSSensor:
    """
    Simulates a direct TPMS sensor unit mounted to the wheel valve stem / rim interior.
    """

    def __init__(self, tyre_id: str, sensor_id: str = None, baseline_pressure_psi: float = 32.0):
        self.tyre_id = tyre_id  # "FL", "FR", "RL", "RR"
        self.sensor_id = sensor_id or f"TPMS-{tyre_id}-{random.randint(1000, 9999):04X}"
        self.baseline_pressure_psi = baseline_pressure_psi
        self.battery_voltage = 3.05  # Standard 3.0V lithium coin cell (CR2032)
        self.battery_health_pct = 98.0
        self.rf_frequency_mhz = 433.92
        self.rssi_dbm = -65  # Radio Signal Strength Indicator (-40 to -90 dBm)
        self.sequence_number = 0
        self.is_active = True
        self.last_transmission_time = time.time()

    def read_pressure_packet(self, true_pressure_psi: float, add_noise: bool = True) -> Dict[str, Any]:
        """
        Samples the transducer and generates an encoded RF telemetry packet.
        """
        self.sequence_number = (self.sequence_number + 1) % 65536
        self.last_transmission_time = time.time()

        # Add physical sensor noise and ADC quantization if enabled
        noise = random.gauss(0.0, 0.08) if add_noise else 0.0
        measured_psi = max(0.0, round(true_pressure_psi + noise, 2))

        # Battery micro-consumption
        self.battery_voltage = max(2.1, self.battery_voltage - 0.000001)
        self.battery_health_pct = max(0.0, round((self.battery_voltage - 2.0) / (3.1 - 2.0) * 100, 1))

        # Fluctuate RSSI slightly to reflect realistic RF multipath
        self.rssi_dbm = int(-65 + random.uniform(-4, 4))

        packet = {
            "sensor_id": self.sensor_id,
            "tyre_id": self.tyre_id,
            "pressure_psi": measured_psi,
            "pressure_bar": round(measured_psi * 0.0689476, 3),
            "pressure_kpa": round(measured_psi * 6.89476, 1),
            "battery_voltage": round(self.battery_voltage, 2),
            "battery_health_pct": self.battery_health_pct,
            "rf_freq_mhz": self.rf_frequency_mhz,
            "rssi_dbm": self.rssi_dbm,
            "seq": self.sequence_number,
            "status": "OK" if self.battery_voltage > 2.3 else "LOW_BATTERY",
            "timestamp": time.time()
        }
        return packet
