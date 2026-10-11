"""
Predictive Tyre Monitoring System (PTMS) - Tyre Physical Model
Models thermodynamic and pneumatic behaviour of automotive radial tyres:
- P-V-T ideal gas relationship with thermal expansion
- Sidewall deflection & hysteretic heat dissipation under low pressure
- Puncture, bead leakage, thermal runaway, and over-pressure fault dynamics
"""

import math
from typing import Dict, Any


class TyreModel:
    """
    Simulates the continuous physical state of a single automotive tyre.
    """

    # Fault mode constants
    FAULT_NORMAL = "NORMAL"
    FAULT_SLOW_LEAK = "SLOW_LEAK"
    FAULT_RAPID_LEAK = "RAPID_LEAK"
    FAULT_LOW_PRESSURE = "LOW_PRESSURE"
    FAULT_HIGH_PRESSURE = "HIGH_PRESSURE"
    FAULT_OVERHEATING = "OVERHEATING"
    FAULT_COMBINED = "COMBINED_FAULT"

    def __init__(self, tyre_id: str, nominal_pressure: float = 32.0, ambient_temp: float = 28.0):
        self.tyre_id = tyre_id  # "FL", "FR", "RL", "RR"
        self.nominal_pressure = nominal_pressure
        self.ambient_temp = ambient_temp

        # Dynamic state variables
        self.pressure_psi = nominal_pressure
        self.temperature_c = ambient_temp + 5.0  # Warm tyre after initial driving
        self.fault_mode = self.FAULT_NORMAL
        self.severity = 0.5  # 0.0 to 1.0

        # Physical constants
        self.gas_temp_coefficient = 0.12  # PSI rise per °C increase
        self.volume_litres = 28.0
        self.vehicle_speed_kmh = 75.0  # Simulated highway cruise

        # Track derivatives
        self.pressure_rate = 0.0  # dP/dt (PSI/sec)
        self.temp_rate = 0.0      # dT/dt (°C/sec)

    def set_fault(self, fault_mode: str, severity: float = 0.5):
        """Injects or resets a simulated physical tyre fault."""
        self.fault_mode = fault_mode
        self.severity = max(0.0, min(1.0, severity))

        if fault_mode == self.FAULT_LOW_PRESSURE:
            self.pressure_psi = 24.0 - (6.0 * self.severity)
        elif fault_mode == self.FAULT_HIGH_PRESSURE:
            self.pressure_psi = 39.0 + (10.0 * self.severity)
        elif fault_mode == self.FAULT_NORMAL:
            pass  # Will smoothly recover toward nominal

    def reset_to_nominal(self):
        """Restores tyre to optimal operating conditions."""
        self.fault_mode = self.FAULT_NORMAL
        self.severity = 0.0
        self.pressure_psi = self.nominal_pressure
        self.temperature_c = self.ambient_temp + 5.0
        self.pressure_rate = 0.0
        self.temp_rate = 0.0

    def update(self, dt: float, speed_multiplier: float = 1.0):
        """
        Advances the physical simulation by dt seconds with speed factor.
        """
        eff_dt = dt * speed_multiplier
        prev_pressure = self.pressure_psi
        prev_temp = self.temperature_c

        # 1. Base thermal equilibrium at current speed
        base_thermal_rise = (self.vehicle_speed_kmh / 100.0) * 8.0
        target_temp = self.ambient_temp + base_thermal_rise

        # 2. Hysteretic Sidewall Flexing (Key tyre physics: when pressure is low, tyre flexes more, dissipating heat)
        pressure_deficit = max(0.0, self.nominal_pressure - self.pressure_psi)
        if pressure_deficit > 0:
            flex_heating = 1.2 * math.pow(pressure_deficit, 1.25)
            target_temp += flex_heating

        # 3. Fault-specific physical dynamics
        leak_rate = 0.0

        if self.fault_mode == self.FAULT_SLOW_LEAK:
            # Gradual pinhole or valve core bead leak: 0.06 to 0.18 PSI/sec in simulated time
            leak_rate = (0.06 + 0.15 * self.severity)
            # Pressure drops, flexing increases heating
            target_temp += 12.0 * self.severity

        elif self.fault_mode == self.FAULT_RAPID_LEAK:
            # Puncture / nail tear: 0.6 to 1.8 PSI/sec
            leak_rate = (0.6 + 1.2 * self.severity)

        elif self.fault_mode == self.FAULT_OVERHEATING:
            # Sticking brake shoe or bearing heat transfer: up to 85-98°C
            target_temp += 35.0 + 35.0 * self.severity

        elif self.fault_mode == self.FAULT_COMBINED:
            # Simultaneous leak and excessive friction
            leak_rate = (0.08 + 0.12 * self.severity)
            target_temp += 30.0 + 25.0 * self.severity

        elif self.fault_mode == self.FAULT_LOW_PRESSURE:
            # Under-inflation: causes persistent sidewall flex heat
            target_temp += 15.0 * self.severity

        elif self.fault_mode == self.FAULT_HIGH_PRESSURE:
            # Stiff tyre, less flexing
            target_temp -= 2.0

        # Apply leak rate
        if leak_rate > 0:
            self.pressure_psi = max(10.0, self.pressure_psi - leak_rate * eff_dt)
        elif self.fault_mode == self.FAULT_NORMAL:
            # Gradual natural return toward nominal if no leak
            if abs(self.pressure_psi - self.nominal_pressure) > 0.1:
                self.pressure_psi += (self.nominal_pressure - self.pressure_psi) * 0.05 * eff_dt

        # Thermal inertia (exponential approach to target temp)
        thermal_rate = 0.15 * eff_dt
        self.temperature_c += (target_temp - self.temperature_c) * min(1.0, thermal_rate)

        # Thermal expansion coupling (Ideal gas law effect: ~0.12 PSI / °C deviation from 30°C)
        thermal_psi_delta = (self.temperature_c - 30.0) * self.gas_temp_coefficient * 0.02 * eff_dt
        if self.fault_mode not in (self.FAULT_SLOW_LEAK, self.FAULT_RAPID_LEAK, self.FAULT_COMBINED):
            self.pressure_psi += thermal_psi_delta

        # Clamp physical limits
        self.pressure_psi = max(8.0, min(55.0, self.pressure_psi))
        self.temperature_c = max(10.0, min(120.0, self.temperature_c))

        # Compute instantaneous rates
        if eff_dt > 0:
            self.pressure_rate = (self.pressure_psi - prev_pressure) / eff_dt
            self.temp_rate = (self.temperature_c - prev_temp) / eff_dt

    def get_state(self) -> Dict[str, Any]:
        """Returns the true physical state snapshot."""
        return {
            "tyre_id": self.tyre_id,
            "pressure_psi": round(self.pressure_psi, 2),
            "temperature_c": round(self.temperature_c, 2),
            "pressure_rate": round(self.pressure_rate, 4),
            "temp_rate": round(self.temp_rate, 4),
            "fault_mode": self.fault_mode,
            "severity": self.severity
        }
