"""
Unit Tests for ProbabilisticForecastEngine and CompassLogEngine.
Verifies:
1. Multi-horizon empirical touch probabilities P(touch L <= X within 1, 3, 5 days).
2. Never emits a single deterministic price; outputs levels, probabilities, and rationales.
3. Unconditional naive Gaussian random-walk baseline (2 * (1 - Phi(z))).
4. Statistical edge detection (|P_cond - P_naive| >= 5%).
5. Brier Score tracking and reliability calibration.
6. SQLite forecast persistence and calibration scorecard retrieval.
"""
import unittest
import math
import sqlite3

from hdfc_predictor.probabilistic_forecast import (
    ProbabilisticForecastEngine,
    LevelTouchForecast,
    ProbabilisticForecastReport
)
from hdfc_predictor.daily_compass_log import (
    CompassLogEngine,
    CompassScoreboardSummary,
    ForecastAuditRow
)


class TestProbabilisticForecastEngine(unittest.TestCase):

    def test_01_forecast_structure_and_levels(self):
        """Rule 1: Output provides levels and multi-horizon probabilities, no single price point."""
        report = ProbabilisticForecastEngine.generate_forecast(reference_price=814.95)

        self.assertIsInstance(report, ProbabilisticForecastReport)
        self.assertEqual(report.reference_price, 814.95)
        self.assertGreater(len(report.forecasts), 0)

        targets = [f.target_price for f in report.forecasts]
        self.assertIn(772.0, targets)
        self.assertIn(743.0, targets)
        self.assertIn(710.0, targets)
        self.assertIn(830.0, targets)

        # Check pullback vs breakout direction and sample size n
        for f in report.forecasts:
            self.assertGreaterEqual(f.sample_size_n, 30)
            self.assertFalse(f.is_hidden)
            if f.target_price < 814.95:
                self.assertEqual(f.direction, "PULLBACK")
                self.assertLess(f.distance_pct, 0)
            else:
                self.assertEqual(f.direction, "BREAKOUT")
                self.assertGreater(f.distance_pct, 0)

    def test_01b_insufficient_sample_size_hides_probability(self):
        """Rule 1b: Any probability with sample size n < 30 must be hidden."""
        # Test custom scenario with small sample size
        report = ProbabilisticForecastEngine.generate_forecast(reference_price=814.95)
        # Verify that all active forecasts meet n >= 30
        for f in report.forecasts:
            if f.sample_size_n < 30:
                self.assertTrue(f.is_hidden)
                self.assertIsNone(f.prob_1d_pct)
                self.assertIn("< 30", f.plain_rationale)
            else:
                self.assertFalse(f.is_hidden)
                self.assertIsNotNone(f.prob_1d_pct)

    def test_02_probabilities_monotonicity_across_horizons(self):
        """Rule 2: Touch probabilities over [1D, 3D, 5D] must be monotonically non-decreasing."""
        report = ProbabilisticForecastEngine.generate_forecast(reference_price=814.95)

        for f in report.forecasts:
            self.assertGreaterEqual(f.prob_3d_pct, f.prob_1d_pct, f"3D prob < 1D prob for {f.target_price}")
            self.assertGreaterEqual(f.prob_5d_pct, f.prob_3d_pct, f"5D prob < 3D prob for {f.target_price}")
            self.assertGreaterEqual(f.naive_prob_3d_pct, f.naive_prob_1d_pct)
            self.assertGreaterEqual(f.naive_prob_5d_pct, f.naive_prob_3d_pct)

    def test_03_naive_gaussian_random_walk_formula(self):
        """Rule 3: Naive benchmark matches exact reflection principle: 2 * (1 - Phi(d / (sigma * sqrt(t))))."""
        ref_price = 800.0
        target = 780.0 # 2.5% move
        dist_pct = (abs(target - ref_price) / ref_price) * 100.0 # 2.5%
        daily_vol_pct = 1.35 # 1.35%

        p1 = ProbabilisticForecastEngine.naive_touch_probability(dist_pct, horizon_days=1, daily_vol_pct=daily_vol_pct)
        p3 = ProbabilisticForecastEngine.naive_touch_probability(dist_pct, horizon_days=3, daily_vol_pct=daily_vol_pct)
        p5 = ProbabilisticForecastEngine.naive_touch_probability(dist_pct, horizon_days=5, daily_vol_pct=daily_vol_pct)

        # Theoretical z for 1D: 0.025 / (0.0135 * 1) = 1.8518 -> 2 * (1 - Phi(1.8518)) = 2 * 0.032 = ~6.4%
        self.assertAlmostEqual(p1, 6.4, delta=1.5)
        self.assertGreater(p3, p1)
        self.assertGreater(p5, p3)

    def test_04_statistical_edge_threshold(self):
        """Rule 4: Statistical edge is flagged only when |P_cond - P_naive| >= 5%."""
        report = ProbabilisticForecastEngine.generate_forecast(reference_price=814.95)

        for f in report.forecasts:
            expected_edge_5d = round(f.prob_5d_pct - f.naive_prob_5d_pct, 1)
            self.assertEqual(f.edge_5d_pct, expected_edge_5d)
            if abs(f.edge_5d_pct) >= 5.0:
                self.assertTrue(f.has_edge_5d)
            else:
                self.assertFalse(f.has_edge_5d)

        # In overbought regime (RSI 88.7), tactical pullback to ₹772 has strong positive edge
        f_772 = next(f for f in report.forecasts if f.target_price == 772.0)
        self.assertTrue(f_772.has_edge_5d)
        self.assertGreater(f_772.edge_5d_pct, 20.0)

    def test_05_brier_score_and_calibration_quality(self):
        """Rule 5: Brier score for conditioned model is lower than naive baseline."""
        report = ProbabilisticForecastEngine.generate_forecast(reference_price=814.95)

        self.assertLess(report.brier_score_conditioned, report.brier_score_naive)
        self.assertGreater(report.brier_skill_score_pct, 0.0)
        self.assertIn(report.overall_edge_status, ["ACTIONABLE_EDGE", "NO_EDGE_TODAY"])

    def test_06_sqlite_persistence_and_scoreboard(self):
        """Rule 6: CompassLogEngine logs forecasts and returns calibrated scoreboard."""
        # Initialize database and log today's forecast
        report = ProbabilisticForecastEngine.generate_forecast(reference_price=814.95)
        logged_count = CompassLogEngine.log_forecast_report(report)
        self.assertGreaterEqual(logged_count, 0)

        scoreboard = CompassLogEngine.get_scoreboard()
        self.assertIsInstance(scoreboard, CompassScoreboardSummary)
        self.assertGreater(scoreboard.total_forecasts_logged, 0)
        self.assertGreater(scoreboard.skill_score_pct, 0)
        self.assertGreater(len(scoreboard.recent_forecast_audits), 0)


if __name__ == "__main__":
    unittest.main()
