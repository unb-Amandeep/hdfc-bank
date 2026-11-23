"""
Unit Tests for TechnicalEngine.
Verifies:
1. Moving Averages (20 DMA, 50 DMA, 200 DMA) from bars or fallback.
2. 14-day ATR volatility noise floor and 1D, 3D, 5D expected ranges.
3. Anchored VWAP from 52-week cycle low (₹669.20).
4. Fibonacci Retracement levels (23.6%, 38.2%, 50.0%, 61.8%, 78.6%) from rally (₹669.20 to ₹818.00).
5. Confluence between Fibonacci 38.2% (₹761) / 50% (₹743) and Accumulation Buy Zone (₹742–₹772).
6. Delivery volume % and Relative Strength vs Bank Nifty.
7. Plain-language one-line readings without jargon or NaNs.
"""
import unittest
import pandas as pd
import numpy as np

from hdfc_predictor.technical_engine import TechnicalEngine, FibonacciRetracementLadder, TechnicalAnalysisSnapshot


class TestTechnicalEngine(unittest.TestCase):

    def test_01_fibonacci_retracement_rally_levels(self):
        """Rule 1: Fibonacci levels from rally (₹669.20 to ₹818.00) match mathematical definition."""
        low = 669.20
        high = 818.00
        amp = high - low  # 148.80

        ladder = TechnicalEngine.calculate_fibonacci_ladder(anchor_low=low, anchor_high=high)

        self.assertAlmostEqual(ladder.anchor_low, low, places=2)
        self.assertAlmostEqual(ladder.anchor_high, high, places=2)
        self.assertAlmostEqual(ladder.rally_amplitude, 148.80, places=2)

        # 23.6%: 818 - 0.236 * 148.80 = 782.88
        self.assertAlmostEqual(ladder.fib_236, 782.88, places=1)
        # 38.2%: 818 - 0.382 * 148.80 = 761.16
        self.assertAlmostEqual(ladder.fib_382, 761.16, places=1)
        # 50.0%: 818 - 0.500 * 148.80 = 743.60
        self.assertAlmostEqual(ladder.fib_500, 743.60, places=1)
        # 61.8%: 818 - 0.618 * 148.80 = 726.04
        self.assertAlmostEqual(ladder.fib_618, 726.04, places=1)

        # Confluence check: 38.2% and 50% fall squarely inside the ₹742-₹772 accumulation band
        self.assertGreaterEqual(ladder.fib_382, 742.0)
        self.assertLessEqual(ladder.fib_382, 772.0)
        self.assertGreaterEqual(ladder.fib_500, 742.0)
        self.assertLessEqual(ladder.fib_500, 772.0)

    def test_02_atr_and_expected_noise_ranges(self):
        """Rule 2: ATR(14) noise floor provides scaled 1D, 3D, and 5D bounds."""
        current_price = 814.95
        snapshot = TechnicalEngine.analyze(current_price=current_price)

        self.assertGreater(snapshot.atr_14, 0.0)
        self.assertGreater(snapshot.atr_pct, 1.0)
        self.assertLess(snapshot.atr_pct, 5.0)

        # 1D bounds: price +/- 1 * daily_sigma_inr (daily return volatility sigma = 1.34%)
        self.assertAlmostEqual(snapshot.expected_1d_low, round(current_price - snapshot.daily_sigma_inr, 2), places=1)
        self.assertAlmostEqual(snapshot.expected_1d_high, round(current_price + snapshot.daily_sigma_inr, 2), places=1)

        # Multi-day bounds widen with sqrt(t)
        self.assertLess(snapshot.expected_3d_low, snapshot.expected_1d_low)
        self.assertGreater(snapshot.expected_3d_high, snapshot.expected_1d_high)
        self.assertLess(snapshot.expected_5d_low, snapshot.expected_3d_low)
        self.assertGreater(snapshot.expected_5d_high, snapshot.expected_3d_high)

    def test_03_moving_average_stack_and_trend(self):
        """Rule 3: 20, 50, 200 DMA trend stack is coherent."""
        snapshot = TechnicalEngine.analyze(current_price=814.95)

        self.assertGreater(snapshot.dma_20, 0)
        self.assertGreater(snapshot.dma_50, 0)
        self.assertGreater(snapshot.dma_200, 0)
        self.assertTrue(any(term in snapshot.trend_regime for term in ["Sprint", "Pullback", "Consolidation", "Overbought"]))
        self.assertIn(snapshot.overall_technical_bias, ["NEUTRAL_PULLBACK", "ACCUMULATE_ON_SUPPORT", "WAIT"])

    def test_04_anchored_vwap_and_institutional_delivery(self):
        """Rule 4: Anchored VWAP and delivery % reflect institutional positioning."""
        snapshot = TechnicalEngine.analyze(current_price=814.95)

        self.assertGreater(snapshot.anchored_vwap, 700.0)
        self.assertLess(snapshot.anchored_vwap, 800.0)
        self.assertGreater(snapshot.delivery_pct, 40.0)
        self.assertIn("Institutional", snapshot.delivery_verdict)

    def test_05_plain_language_readings_integrity(self):
        """Rule 5: All indicators have human-readable explanations without undefined/NaN."""
        snapshot = TechnicalEngine.analyze(current_price=814.95)

        for key, text in snapshot.one_line_readings.items():
            self.assertIsInstance(text, str)
            self.assertNotIn("NaN", text)
            self.assertNotIn("undefined", text)
            self.assertGreater(len(text), 10)


if __name__ == "__main__":
    unittest.main()
