"""
Predictive Tyre Monitoring System (PTMS) - Multi-Factor Risk Engine
Computes holistic risk score (0-100%) and predictive diagnostics.
Thresholds:
- 0–20%: SAFE
- 21–40%: NORMAL
- 41–60%: CAUTION
- 61–80%: WARNING
- 81–100%: CRITICAL
"""

from typing import Dict, Any, Tuple


class RiskEngine:
    """
    Evaluates multi-parametric tyre health combining absolute values,
    derivatives (rates), and axle imbalance.
    """

    # Status constants
    STATUS_SAFE = "SAFE"
    STATUS_NORMAL = "NORMAL"
    STATUS_CAUTION = "CAUTION"
    STATUS_WARNING = "WARNING"
    STATUS_CRITICAL = "CRITICAL"

    def __init__(self, nominal_pressure: float = 32.0):
        self.nominal_pressure = nominal_pressure

    def evaluate_tyre(self, pressure: float, temperature: float,
                      pressure_rate_min: float, temp_rate_min: float,
                      axle_delta_psi: float) -> Dict[str, Any]:
        """
        Evaluates a single tyre and returns risk score (0-100), status, prediction,
        and recommended action.
        """
        risk = 5.0  # Base healthy baseline
        diagnostics = []
        recommendation = "Tyre operating within optimal parameters."

        # 1. Absolute Pressure Deviation Penalty
        p_deviation = pressure - self.nominal_pressure

        if p_deviation < -10.0:  # < 22 PSI
            risk += 50.0
            diagnostics.append("Severe under-inflation")
        elif p_deviation < -6.0:  # < 26 PSI
            risk += 35.0
            diagnostics.append("Significant under-inflation")
        elif p_deviation < -3.0:  # < 29 PSI
            risk += 18.0
            diagnostics.append("Moderate pressure deficit")
        elif p_deviation > 8.0:   # > 40 PSI
            risk += 28.0
            diagnostics.append("High over-inflation")
        elif p_deviation > 5.0:   # > 37 PSI
            risk += 14.0
            diagnostics.append("Mild over-inflation")

        # 2. Predictive Rate Penalty (dP/dt) - CRITICAL FOR EARLY DETECTION
        # pressure_rate_min is in PSI/min (negative means losing pressure)
        if pressure_rate_min < -15.0:
            risk += 55.0
            diagnostics.append("Rapid pressure blowout risk")
        elif pressure_rate_min < -5.0:
            risk += 40.0
            diagnostics.append("Fast leak detected")
        elif pressure_rate_min < -1.0:
            risk += 26.0
            diagnostics.append("Gradual pressure loss detected")
        elif pressure_rate_min < -0.3:
            risk += 14.0
            diagnostics.append("Subtle negative pressure drift")

        # 3. Temperature & Thermal Rate Penalty (dT/dt)
        if temperature > 80.0:
            risk += 45.0
            diagnostics.append("Severe thermal stress (>80°C)")
        elif temperature > 65.0:
            risk += 25.0
            diagnostics.append("High operating temperature (>65°C)")
        elif temperature > 50.0:
            risk += 10.0
            diagnostics.append("Elevated temperature")

        if temp_rate_min > 4.0:
            risk += 25.0
            diagnostics.append("Rapid thermal rise rate")
        elif temp_rate_min > 1.5:
            risk += 12.0
            diagnostics.append("Positive thermal acceleration")

        # 4. Cross-Coupled Fault Penalty: Low Pressure + Rising Temp (Classic Sidewall Flex Runaway)
        if (pressure < 30.0) and (temp_rate_min > 0.8 or temperature > 42.0):
            risk += 18.0
            diagnostics.append("Sidewall flex heat accumulation")

        # 5. Axle Imbalance Penalty (e.g. RL vs RR difference)
        if axle_delta_psi > 5.0:
            risk += 20.0
            diagnostics.append(f"Significant axle imbalance ({axle_delta_psi:.1f} PSI diff)")
        elif axle_delta_psi > 3.0:
            risk += 10.0
            diagnostics.append(f"Moderate axle imbalance ({axle_delta_psi:.1f} PSI diff)")

        # Clamp Risk Score to [0, 100]
        final_risk = max(0.0, min(100.0, risk))

        # Status Classification
        if final_risk <= 20.0:
            status = self.STATUS_SAFE
            recommendation = "All parameters safe. Continue normal driving."
        elif final_risk <= 40.0:
            status = self.STATUS_NORMAL
            recommendation = "Minor nominal fluctuation. No intervention needed."
        elif final_risk <= 60.0:
            status = self.STATUS_CAUTION
            recommendation = "Pressure/temperature deviation observed. Monitor trend."
        elif final_risk <= 80.0:
            status = self.STATUS_WARNING
            recommendation = "PREDICTED TYRE FAILURE RISK: Inspection recommended soon."
        else:
            status = self.STATUS_CRITICAL
            recommendation = "CRITICAL HAZARD: Stop vehicle safely and inspect tyre immediately!"

        primary_diagnosis = "; ".join(diagnostics) if diagnostics else "Nominal operating condition"

        return {
            "risk_score": round(final_risk, 1),
            "status": status,
            "prediction": primary_diagnosis,
            "recommendation": recommendation,
            "diagnostics": diagnostics
        }
