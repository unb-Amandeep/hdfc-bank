"""
Unit test for Gate 3: Computed Base Formation & Falling Knife Rejection.
Verifies that an engineered falling-knife price series strictly fails Gate 3.
"""
import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from hdfc_predictor.accumulation_gates import AccumulationGatesEngine


class TestFallingKnifeGate3(unittest.TestCase):
    def test_falling_knife_series_must_fail_gate_3(self):
        """
        Constructs an aggressive downward trending series with consecutive lower lows
        and a steep negative 50-DMA slope. Gate 3 MUST evaluate to status='ABSTAIN' and passed=False.
        """
        np.random.seed(42)
        n = 100
        dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(n)]

        # Engineered falling knife: Starting at 1000, plunging down to 500 linearly with noise
        base_prices = np.linspace(1000.0, 500.0, n)
        closes = base_prices + np.random.normal(0, 2.0, n)
        lows = closes - np.random.uniform(2.0, 5.0, n)
        highs = closes + np.random.uniform(2.0, 5.0, n)

        df_falling_knife = pd.DataFrame({
            "Date": dates,
            "Open": closes + 1.0,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": 1000000
        })

        res = AccumulationGatesEngine.evaluate_gate_3_base_formation(df_bars=df_falling_knife)
        
        self.assertFalse(res.passed, "Gate 3 must fail on a steep falling knife series")
        self.assertEqual(res.status, "ABSTAIN", "Gate 3 status must be ABSTAIN on falling knife")
        self.assertEqual(res.action_directive, "ABSTAIN_FALLING_KNIFE")
        self.assertTrue(res.evidence_metrics["is_falling_knife"], "Falling knife flag must be True")

    def test_consolidating_base_series_passes_gate_3(self):
        """
        Constructs a base-building series with higher lows and a stabilizing 50-DMA.
        Gate 3 MUST pass.
        """
        n = 100
        dates = [datetime(2026, 1, 1) + timedelta(days=i) for i in range(n)]
        
        # Base building: dropped to 700 at day 50, then rounded upward to 760 with higher lows
        p1 = np.linspace(850.0, 700.0, 50)
        p2 = np.linspace(700.0, 760.0, 50)
        closes = np.concatenate([p1, p2])
        lows = closes - 3.0
        highs = closes + 3.0

        df_base = pd.DataFrame({
            "Date": dates,
            "Open": closes,
            "High": highs,
            "Low": lows,
            "Close": closes,
            "Volume": 1000000
        })

        res = AccumulationGatesEngine.evaluate_gate_3_base_formation(df_bars=df_base)
        self.assertTrue(res.passed, "Gate 3 must pass on a base formation with higher lows")
        self.assertEqual(res.status, "PASS")


if __name__ == "__main__":
    unittest.main()
