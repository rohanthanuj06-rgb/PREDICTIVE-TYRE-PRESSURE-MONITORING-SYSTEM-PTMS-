"""
Predictive Tyre Monitoring System (PTMS) - Trend Analysis Engine
Computes moving window statistical derivatives, slope analysis (dP/dt, dT/dt),
and cross-axle tyre symmetry deviations.
"""

from collections import deque
from typing import Dict, List, Tuple
import numpy as np


class TyreTrendTracker:
    """
    Maintains a rolling temporal window of telemetry for a single tyre
    and calculates linear regression rates and acceleration derivatives.
    """

    def __init__(self, window_size: int = 30):
        self.window_size = window_size
        self.timestamps: deque = deque(maxlen=window_size)
        self.pressures: deque = deque(maxlen=window_size)
        self.temperatures: deque = deque(maxlen=window_size)

    def add_reading(self, timestamp: float, pressure: float, temperature: float):
        self.timestamps.append(timestamp)
        self.pressures.append(pressure)
        self.temperatures.append(temperature)

    def get_pressure_rate_psi_per_min(self) -> float:
        """
        Calculates dP/dt in PSI per minute using robust linear regression.
        Negative indicates pressure loss.
        """
        if len(self.pressures) < 4:
            return 0.0

        t = np.array(self.timestamps)
        t_norm = (t - t[0])  # seconds from first sample in window
        if t_norm[-1] <= 0:
            return 0.0

        p = np.array(self.pressures)
        # Linear fit slope: PSI per second
        slope, _ = np.polyfit(t_norm, p, 1)
        # Convert to PSI per minute
        return float(slope * 60.0)

    def get_temperature_rate_c_per_min(self) -> float:
        """
        Calculates dT/dt in °C per minute using linear regression.
        Positive indicates heat build-up.
        """
        if len(self.temperatures) < 4:
            return 0.0

        t = np.array(self.timestamps)
        t_norm = (t - t[0])
        if t_norm[-1] <= 0:
            return 0.0

        temps = np.array(self.temperatures)
        slope, _ = np.polyfit(t_norm, temps, 1)
        return float(slope * 60.0)

    def get_pressure_variance(self) -> float:
        if len(self.pressures) < 3:
            return 0.0
        return float(np.var(self.pressures))


class TrendAnalysisEngine:
    """
    Aggregates multi-tyre trends and axle balance comparisons (FL vs FR, RL vs RR).
    """

    def __init__(self, window_size: int = 30):
        self.trackers: Dict[str, TyreTrendTracker] = {
            "FL": TyreTrendTracker(window_size),
            "FR": TyreTrendTracker(window_size),
            "RL": TyreTrendTracker(window_size),
            "RR": TyreTrendTracker(window_size)
        }

    def update(self, timestamp: float, readings: Dict[str, Dict[str, float]]):
        """Feeds new reading frames for all 4 tyres."""
        for tid, data in readings.items():
            if tid in self.trackers:
                self.trackers[tid].add_reading(
                    timestamp,
                    data["pressure_psi"],
                    data["temperature_c"]
                )

    def analyze_trends(self, current_pressures: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """
        Analyzes rates and axle imbalance for all tyres.
        """
        results = {}

        # Axle counterparts for differential pressure comparison
        counterparts = {
            "FL": "FR",
            "FR": "FL",
            "RL": "RR",
            "RR": "RL"
        }

        for tid, tracker in self.trackers.items():
            dP_dt = tracker.get_pressure_rate_psi_per_min()
            dT_dt = tracker.get_temperature_rate_c_per_min()

            # Axle differential (e.g. RL vs RR)
            peer_id = counterparts.get(tid)
            peer_p = current_pressures.get(peer_id, current_pressures.get(tid, 32.0))
            axle_delta_psi = abs(current_pressures.get(tid, 32.0) - peer_p)

            results[tid] = {
                "pressure_rate_psi_min": round(dP_dt, 3),
                "temp_rate_c_min": round(dT_dt, 3),
                "axle_delta_psi": round(axle_delta_psi, 2),
                "pressure_variance": round(tracker.get_pressure_variance(), 4)
            }

        return results
