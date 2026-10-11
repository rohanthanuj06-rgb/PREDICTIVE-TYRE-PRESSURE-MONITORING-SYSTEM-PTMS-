"""
Predictive Tyre Monitoring System (PTMS) - Temperature Sensor Module
Simulates digital high-precision temperature sensing (DS18B20 1-Wire / IR tyre surface probe).
Features:
- Resolution: 0.0625°C (12-bit DS18B20 equivalent)
- Thermal inertia & sensor lag simulation
- Measurement range: -40°C to +125°C
"""

import random
import time
from typing import Dict, Any


class TemperatureSensor:
    """
    Simulates a digital tyre temperature probe (DS18B20 architecture).
    """

    def __init__(self, tyre_id: str, sensor_id: str = None, baseline_temp_c: float = 32.0):
        self.tyre_id = tyre_id
        self.sensor_id = sensor_id or f"DS18B20-{tyre_id}-{random.randint(100, 999)}"
        self.baseline_temp_c = baseline_temp_c
        self.current_filtered_temp_c = baseline_temp_c
        self.thermal_tau = 0.85  # Exponential smoothing filter constant
        self.is_active = True

    def read_temperature_packet(self, true_temp_c: float, add_noise: bool = True) -> Dict[str, Any]:
        """
        Samples the thermal element with digital 1-Wire quantization and sensor lag.
        """
        # Sensor lag (thermal mass of metal housing)
        self.current_filtered_temp_c = (
            self.thermal_tau * self.current_filtered_temp_c + (1.0 - self.thermal_tau) * true_temp_c
        )

        noise = random.gauss(0.0, 0.05) if add_noise else 0.0
        # 12-bit DS18B20 quantization step = 0.0625°C
        quantized_temp = round(round((self.current_filtered_temp_c + noise) / 0.0625) * 0.0625, 2)
        temp_f = round(quantized_temp * 9.0 / 5.0 + 32.0, 1)

        return {
            "sensor_id": self.sensor_id,
            "tyre_id": self.tyre_id,
            "temp_c": quantized_temp,
            "temp_f": temp_f,
            "status": "NORMAL" if quantized_temp < 60.0 else ("WARNING" if quantized_temp < 75.0 else "OVERHEAT"),
            "timestamp": time.time()
        }
