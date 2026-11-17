"""
Unit tests for Phase 5: Fair Value, Quantitative Regime, and Tier Arbitration.
"""
import unittest

from hdfc_predictor.fair_value_and_regime import FairValueAndRegimeEngine, RegimeState, ArbitrationDirective
from hdfc_predictor.fundamental_engine import FundamentalEngine


class TestPhase5FairValueAndRegime(unittest.TestCase):
    def setUp(self):
        self.engine = FairValueAndRegimeEngine()
        self.fundamental_engine = FundamentalEngine()

    def test_justified_pb_scenarios_and_merger_break(self):
        """Tests that justified P/B residual income model generates 3 scenarios summing to 100% prob."""
        report = self.engine.compute_justified_fair_value(current_price=814.0, book_value_per_share=394.84)
        
        self.assertEqual(len(report.scenarios), 3)
        total_prob = sum(s.probability for s in report.scenarios)
        self.assertAlmostEqual(total_prob, 1.0, places=4)
        
        # Verify post-merger structural break window is explicitly isolated
        self.assertIn("Post-Merger Regime", report.merger_structural_break_window)
        self.assertIn("July 2023", report.merger_structural_break_window)
        
        # Check scenario ordering and expected valuations
        bear, base, bull = report.scenarios
        self.assertEqual(bear.scenario_name.split()[0], "BEAR")
        self.assertEqual(base.scenario_name.split()[0], "BASE")
        self.assertEqual(bull.scenario_name.split()[0], "BULL")
        self.assertTrue(bear.fair_value_high < base.fair_value_low)
        self.assertTrue(base.fair_value_high < bull.fair_value_low)
        
        # Margin of safety should be positive if expected fair value > current price
        self.assertGreater(report.weighted_expected_fair_value, 800.0)
        self.assertIsInstance(report.margin_of_safety_pct, float)

    def test_regime_model_deterministic_states(self):
        """Tests 3-state deterministic regime model state transitions without LLM guesses."""
        # 1. Overheated momentum stretch
        s_overheated = self.engine.evaluate_regime_state(
            rsi_14=85.0, dist_sma_20=0.11, dist_sma_50=0.08, vol_ratio=1.2, fundamental_score=80
        )
        self.assertEqual(s_overheated.state_id, "OVERHEATED_OR_BREAKDOWN")
        self.assertIn("Overheated", s_overheated.state_label)
        self.assertLess(s_overheated.historical_forward_30d_return, 0)

        # 2. Structural breakdown (fundamental rot)
        s_breakdown = self.engine.evaluate_regime_state(
            rsi_14=50.0, dist_sma_20=-0.02, dist_sma_50=-0.03, vol_ratio=1.0, fundamental_score=42
        )
        self.assertEqual(s_breakdown.state_id, "OVERHEATED_OR_BREAKDOWN")
        self.assertIn("Structural Fundamental Breakdown", s_breakdown.state_label)
        self.assertLess(s_breakdown.historical_forward_30d_return, -5.0)

        # 3. Active correction
        s_correction = self.engine.evaluate_regime_state(
            rsi_14=34.0, dist_sma_20=-0.04, dist_sma_50=-0.08, vol_ratio=1.1, fundamental_score=80
        )
        self.assertEqual(s_correction.state_id, "CORRECTION")

        # 4. Base recovery
        s_base = self.engine.evaluate_regime_state(
            rsi_14=52.0, dist_sma_20=0.01, dist_sma_50=0.02, vol_ratio=0.95, fundamental_score=82
        )
        self.assertEqual(s_base.state_id, "BASE_RECOVERY")
        self.assertGreater(s_base.historical_forward_30d_return, 0)

    def test_arbitration_tier_conflict_and_limit_order(self):
        """Tests arbitration when Primary wants ACCUMULATE but Tactical flags SELL -> LIMIT_ORDER_PULLBACK."""
        directive = self.engine.arbitrate_decision(
            bottom_opportunity_score=82,
            fundamental_score=85,
            tactical_action="STRONG SELL (TAKE PROFIT)",
            current_price=814.0,
            current_pb=2.06,
            days_to_earnings=45,
            days_to_rbi_mpc=20,
            gift_nifty_change_pct=-0.35
        )
        self.assertTrue(directive.has_tier_conflict)
        self.assertEqual(directive.verdict_action, "WAIT")  # Price (814) > buy zone max (775) -> MUST BE WAIT!
        self.assertEqual(directive.execution_order_type, "LIMIT_ORDER_PULLBACK")
        self.assertEqual(directive.overnight_gift_nifty_bias, "BEARISH")
        self.assertEqual(directive.thesis_break_status, "INTACT")
        self.assertIn("2026-11-24", directive.order_expiry_date)
        self.assertIn("cancel the pending limit order", directive.order_recheck_rule)
        # Pullback limit zone must be strictly below current market price
        self.assertLess(directive.limit_entry_zone[1], 814.0)
        self.assertIn("TIER CONFLICT SURFACED", directive.tier_conflict_explanation)

    def test_arbitration_event_blackout_and_thesis_invalidation(self):
        """Tests event blackout triggers within 2 days of earnings and thesis invalidation on fundamental collapse."""
        # 1. Earnings blackout
        blackout_dir = self.engine.arbitrate_decision(
            bottom_opportunity_score=85,
            fundamental_score=80,
            tactical_action="STRONG BUY",
            current_price=814.0,
            current_pb=2.06,
            days_to_earnings=1,
            days_to_rbi_mpc=15
        )
        self.assertTrue(blackout_dir.is_event_blackout_active)
        self.assertEqual(blackout_dir.execution_order_type, "HOLD_OFF")
        self.assertIn("EVENT BLACKOUT", blackout_dir.blackout_reason)

        # 2. Fundamental thesis invalidation
        inval_dir = self.engine.arbitrate_decision(
            bottom_opportunity_score=75,
            fundamental_score=45,  # Broken fundamentals
            tactical_action="BUY",
            current_price=750.0,
            current_pb=1.90,
            days_to_earnings=30,
            days_to_rbi_mpc=10
        )
        self.assertEqual(inval_dir.thesis_break_status, "INVALIDATED")
        self.assertIn("Thesis invalidated", inval_dir.what_would_change_my_mind)

    def test_expanded_fundamentals_and_hygiene_metadata(self):
        """Tests expanded balance sheet metrics and non-negotiable data hygiene metadata."""
        profile = self.fundamental_engine.get_latest_fundamental_profile()
        
        # Verify expanded metrics are populated
        self.assertTrue(hasattr(profile, "nii_growth_yoy"))
        self.assertTrue(hasattr(profile, "casa_ratio_pct"))
        self.assertTrue(hasattr(profile, "credit_cost_pct"))
        self.assertTrue(hasattr(profile, "slippage_ratio_pct"))
        self.assertTrue(hasattr(profile, "provision_coverage_ratio"))
        self.assertTrue(hasattr(profile, "cost_to_income_ratio_pct"))
        self.assertTrue(hasattr(profile, "liquidity_coverage_ratio_pct"))
        
        # Verify metric metadata: source, as_of_date, entity_scope, is_verified
        self.assertIsNotNone(profile.metric_metadata)
        for key in ["net_interest_margin", "gross_npa_pct", "capital_adequacy_ratio", "credit_cost_pct", "liquidity_coverage_ratio_pct"]:
            self.assertIn(key, profile.metric_metadata)
            meta = profile.metric_metadata[key]
            self.assertIn("source", meta)
            self.assertIn("as_of_date", meta)
            self.assertIn("entity_scope", meta)
            self.assertIn("is_verified", meta)


if __name__ == "__main__":
    unittest.main()
