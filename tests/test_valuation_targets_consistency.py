"""
Automated Consistency Tests for Valuation Targets and Single Source of Truth.
FAILS THE BUILD if two cards or models disagree on targets, upsides, exit rules, or thresholds.
"""
import unittest

from hdfc_predictor.valuation_targets import ValuationTargetEngine, UnifiedValuationLedger


class TestValuationTargetsConsistency(unittest.TestCase):
    def setUp(self):
        self.ref_price = 817.80
        self.ledger = ValuationTargetEngine.compute_unified_targets(reference_price=self.ref_price)

    def test_single_source_of_truth_upside_consistency(self):
        """Tests that all upside percentages strictly equal (target - ref) / ref * 100."""
        # Check scenario upsides
        for sc in self.ledger.scenarios:
            expected_pct = round(((sc.target_price - self.ref_price) / self.ref_price) * 100, 1)
            self.assertEqual(
                sc.upside_vs_reference_pct,
                expected_pct,
                f"Scenario '{sc.name}' upside mismatch: {sc.upside_vs_reference_pct}% vs expected {expected_pct}%"
            )

        # Check multi-horizon upsides
        for h_key, h_tgt in self.ledger.horizon_targets.items():
            expected_pct = round(((h_tgt.target_price - self.ref_price) / self.ref_price) * 100, 1)
            self.assertEqual(
                h_tgt.expected_return_pct,
                expected_pct,
                f"Horizon '{h_key}' upside mismatch: {h_tgt.expected_return_pct}% vs expected {expected_pct}%"
            )

    def test_exit_rule_bounded_by_bull_case_and_structural_break(self):
        """Tests that valuation exit price NEVER exceeds the Bull Case and treats pre-merger P/B as structural break."""
        bull_scenario = [s for s in self.ledger.scenarios if "bull" in s.name.lower()][0]
        
        # Invariant: Exit price must not exceed Bull Case
        self.assertLessEqual(
            self.ledger.valuation_exit_price,
            bull_scenario.target_price,
            f"Valuation exit ({self.ledger.valuation_exit_price}) exceeds Bull Case ({bull_scenario.target_price})!"
        )
        self.assertEqual(self.ledger.valuation_exit_price, bull_scenario.target_price)
        # Pre-merger 3.4x (₹1,340) must NOT be the exit price
        self.assertNotEqual(self.ledger.valuation_exit_price, 1340.0)
        self.assertIn("Structural Break", self.ledger.structural_break_note)

    def test_fair_value_and_120d_target_alignment(self):
        """Tests that 6M/120-day target aligns with Base Fair Value without contradiction."""
        base_scenario = [s for s in self.ledger.scenarios if "base" in s.name.lower()][0]
        tgt_120d = self.ledger.horizon_targets["120d"]

        # Both must target the Base Fair Value
        self.assertEqual(base_scenario.target_price, tgt_120d.target_price)
        self.assertEqual(base_scenario.upside_vs_reference_pct, tgt_120d.expected_return_pct)
        self.assertEqual(self.ledger.base_fair_value, tgt_120d.target_price)

    def test_reference_price_and_horizon_explicitly_stated(self):
        """Tests that every target specifies reference price and horizon name."""
        self.assertGreater(self.ledger.reference_price, 0)
        for h_key, h_tgt in self.ledger.horizon_targets.items():
            self.assertEqual(h_tgt.reference_price, self.ledger.reference_price)
            self.assertTrue(len(h_tgt.horizon_name) > 0)
            self.assertGreater(h_tgt.horizon_trading_days, 0)

    def test_deposit_growth_threshold_uniformity(self):
        """Tests that deposit growth warning threshold is strictly 11.0% everywhere."""
        self.assertEqual(self.ledger.deposit_growth_warning_threshold_pct, 11.0)


if __name__ == "__main__":
    unittest.main()
