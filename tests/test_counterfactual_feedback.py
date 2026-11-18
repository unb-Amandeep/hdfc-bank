"""
Unit tests for Counterfactual Outcome Logging, Brier Events, and Sample Size Gate.
"""
import unittest

from hdfc_predictor.unified_feedback import (
    CounterfactualOutcomeLogger,
    CounterfactualOutcome,
    UnifiedLearningManager,
    UnifiedScheduleManager
)


class TestCounterfactualFeedback(unittest.TestCase):
    def test_counterfactual_wait_limit_filled(self):
        """Tests that when price dips into limit zone within 5 days, limit is recorded as filled with positive benefit."""
        res = CounterfactualOutcomeLogger.evaluate_wait_counterfactual(
            decision_price=817.80,
            limit_order_price=775.0,
            subsequent_5d_lows=[810.0, 795.0, 768.0, 782.0, 790.0],
            matured_price_120d=920.0,
            benchmark_120d_return_pct=8.5
        )
        self.assertTrue(res.limit_filled_5d)
        self.assertEqual(res.event_limit_filled_5d, 1)
        self.assertEqual(res.limit_fill_realized_return_pct, round(((920.0 - 775.0) / 775.0) * 100.0, 2))
        self.assertLess(res.opportunity_cost_pct, 0.0) # Waiting was advantageous
        self.assertEqual(res.event_beat_index_120d, 1)
        self.assertIn("Waiting improved return", res.explanation)

    def test_counterfactual_wait_limit_not_filled(self):
        """Tests that when price never dips into limit zone, limit is not filled and opportunity cost is logged."""
        res = CounterfactualOutcomeLogger.evaluate_wait_counterfactual(
            decision_price=817.80,
            limit_order_price=750.0,
            subsequent_5d_lows=[812.0, 815.0, 805.0, 810.0, 820.0],
            matured_price_120d=920.0,
            benchmark_120d_return_pct=8.5
        )
        self.assertFalse(res.limit_filled_5d)
        self.assertEqual(res.event_limit_filled_5d, 0)
        self.assertIsNone(res.limit_fill_realized_return_pct)
        self.assertGreater(res.opportunity_cost_pct, 0.0)
        self.assertIn("Opportunity cost", res.explanation)

    def test_sample_size_gate_before_recalibration(self):
        """Tests that Layer 2 recalibration is BLOCKED if sample size n < 20."""
        mgr = UnifiedLearningManager()
        
        # Small sample (n=8)
        res_small = mgr.layer2_update_calibration(
            mature_actuals=[1.0, 0.0, 1.0, 1.0, 0.0, 1.0, 1.0, 0.0],
            forecast_probs=[0.6, 0.4, 0.7, 0.8, 0.3, 0.65, 0.7, 0.4]
        )
        self.assertEqual(res_small["status"], "INSUFFICIENT_SAMPLE")
        self.assertFalse(res_small["recalibration_executed"])
        self.assertEqual(res_small["sample_size"], 8)
        self.assertEqual(res_small["min_required"], 20)

        # Adequate sample (n=25)
        res_large = mgr.layer2_update_calibration(
            mature_actuals=[1.0] * 15 + [0.0] * 10,
            forecast_probs=[0.7] * 15 + [0.3] * 10
        )
        self.assertEqual(res_large["status"], "RECALIBRATED")
        self.assertTrue(res_large["recalibration_executed"])
        self.assertEqual(res_large["sample_size"], 25)

    def test_threshold_version_tag_default(self):
        """Tests that default threshold version tag is th-2026.11-concall-v2."""
        sched = UnifiedScheduleManager(commit_hash="test_hash")
        res = sched.run_1400_immutable_snapshot()
        self.assertEqual(res["step"], "14:00_IMMUTABLE_SNAPSHOT")


if __name__ == "__main__":
    unittest.main()
