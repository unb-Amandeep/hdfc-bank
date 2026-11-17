"""
Unit tests for Phase 4: Probabilistic Calibration, Brier Score,
Reliability Curves, and Forward Return Distributions.
"""
import unittest
import numpy as np
import pandas as pd

from hdfc_predictor.probabilistic_calibration import (
    ProbabilisticCalibrationEngine,
    CalibrationAuditReport,
    HorizonDistribution
)


class TestPhase4CalibrationAndDistributions(unittest.TestCase):
    def test_01_brier_and_log_loss_computation(self):
        """Verifies mathematical correctness of Brier score and log loss."""
        # Case A: Perfect forecast (Predicted 1.0 when True, 0.0 when False)
        preds_perfect = np.array([0.999, 0.999, 0.001, 0.001])
        actuals_perfect = np.array([1, 1, 0, 0])
        report_perf = ProbabilisticCalibrationEngine.compute_brier_and_log_loss(preds_perfect, actuals_perfect)
        self.assertAlmostEqual(report_perf.brier_score, 0.0, delta=0.01)
        self.assertEqual(report_perf.calibration_quality, "WELL_CALIBRATED")

        # Case B: Coin toss forecast (0.50 for all)
        preds_coin = np.array([0.5, 0.5, 0.5, 0.5])
        actuals_coin = np.array([1, 0, 1, 0])
        report_coin = ProbabilisticCalibrationEngine.compute_brier_and_log_loss(preds_coin, actuals_coin)
        self.assertAlmostEqual(report_coin.brier_score, 0.25, delta=0.01)
        self.assertAlmostEqual(report_coin.log_loss, 0.693, delta=0.01)

        # Reliability curve bins should exist
        self.assertGreater(len(report_coin.reliability_curve_bins), 0)
        self.assertEqual(report_coin.shrinkage_prior_base_rate, 0.52)

    def test_02_forward_horizon_distributions(self):
        """Verifies distribution generation across all 5 standard horizons."""
        # Generate synthetic price series
        np.random.seed(42)
        dates = pd.date_range("2024-01-01", periods=300, freq="B")
        c = 800.0 * np.cumprod(1 + np.random.normal(0.0004, 0.012, 300))
        df = pd.DataFrame({"Close": c}, index=dates)

        dists = ProbabilisticCalibrationEngine.get_all_horizon_distributions(
            opportunity_score=80,
            price_df=df
        )

        expected_keys = ["horizon_5d", "horizon_20d", "horizon_60d", "horizon_120d", "horizon_252d"]
        for k in expected_keys:
            self.assertIn(k, dists)
            d = dists[k]
            self.assertIsInstance(d, HorizonDistribution)
            self.assertTrue(0.0 <= d.probability_negative_return <= 1.0)
            self.assertTrue(0.0 <= d.probability_beating_bank_nifty <= 1.0)
            # 90% interval check: lower bound < upper bound
            low_90, high_90 = d.uncertainty_interval_90
            self.assertLess(low_90, high_90)

    def test_03_thin_sample_interval_widening(self):
        """Verifies that thin sample sizes trigger interval widening (1.35x)."""
        # Pass empty sample -> thin sample trigger
        d_thin = ProbabilisticCalibrationEngine.generate_forward_distribution(
            horizon_days=252,
            opportunity_score=75,
            historical_returns=np.array([])  # 0 samples
        )
        self.assertTrue(d_thin.is_pooled_peer_adjusted)
        self.assertEqual(d_thin.interval_widening_factor, 1.35)


if __name__ == "__main__":
    unittest.main()
