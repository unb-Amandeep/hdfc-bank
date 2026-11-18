"""
Unit Tests for Downside Distribution Consistency & Limit Tranche Sizing.
Fails if:
1. 90% Confidence Interval lower bound does NOT equal 95% VaR.
2. Downside metrics contradict the single underlying distribution.
3. Limit tranche sizing does not match the 258–268 share calculation for ₹2L.
4. Sensitivity table does not reconcile filing-derived ROE and CAR ratios.
"""
import unittest
import numpy as np
import scipy.stats as st

from hdfc_predictor.valuation_targets import ValuationTargetEngine


class TestDownsideDistributionConsistency(unittest.TestCase):
    def setUp(self):
        self.ref_price = 817.80
        self.ledger = ValuationTargetEngine.compute_unified_targets(reference_price=self.ref_price)
        self.dist = self.ledger.downside_distribution

    def test_var_95_strictly_equals_ci_90_lower(self):
        """Tests that 95% VaR is identically equal to the 5th percentile / 90% CI lower bound."""
        self.assertEqual(
            self.dist.ci_90_lower,
            self.dist.var_95_pct,
            f"Mathematical contradiction: 90% CI lower ({self.dist.ci_90_lower}%) != 95% VaR ({self.dist.var_95_pct}%)"
        )
        # Horizon 120d must match the distribution exactly
        tgt_120d = self.ledger.horizon_targets["120d"]
        self.assertEqual(tgt_120d.confidence_interval_90[0], self.dist.ci_90_lower)
        self.assertEqual(tgt_120d.downside_risk_pct, self.dist.var_95_pct)

    def test_floor_probability_monotonicity_against_var_95(self):
        """Tests that probability of breaching floor respects CDF monotonicity."""
        floor_drop = self.dist.floor_required_drop_pct # e.g. -13.18%
        var_95 = self.dist.var_95_pct                 # e.g. -7.8%

        # Because -13.18% is a deeper drop than -7.8%, prob must be strictly less than 5% (0.05)
        if floor_drop < var_95:
            self.assertLess(
                self.dist.prob_breach_floor_pct,
                5.0,
                f"Floor drop ({floor_drop}%) is worse than 95% VaR ({var_95}%), but prob ({self.dist.prob_breach_floor_pct}%) >= 5%!"
            )
        else:
            self.assertGreater(
                self.dist.prob_breach_floor_pct,
                5.0,
                f"Floor drop ({floor_drop}%) is milder than 95% VaR ({var_95}%), but prob ({self.dist.prob_breach_floor_pct}%) <= 5%!"
            )

    def test_distribution_cdf_mathematical_precision(self):
        """Tests that prob_breach_floor is exactly CDF(z_floor) from the same distribution."""
        z = (self.dist.floor_required_drop_pct - self.dist.expected_return_pct) / self.dist.std_dev_pct
        expected_prob = round(float(st.norm.cdf(z)) * 100.0, 2)
        self.assertAlmostEqual(self.dist.prob_breach_floor_pct, expected_prob, places=1)

    def test_limit_tranche_sizing_accuracy(self):
        """Tests that the first tranche is sized dynamically at the derived limit range for ₹2L."""
        tranche = self.ledger.limit_tranche
        self.assertEqual(tranche.budget_amount, 200000.0)
        self.assertEqual(tranche.shares_at_zone_high, int(tranche.budget_amount // tranche.limit_zone_high))
        self.assertEqual(tranche.shares_at_zone_low, int(tranche.budget_amount // tranche.limit_zone_low))
        self.assertEqual(tranche.shares_range_label, f"{tranche.shares_at_zone_high}–{tranche.shares_at_zone_low} shares")
        self.assertNotIn("We approve buying", tranche.non_conflicting_action_text)
        self.assertIn("limit order", tranche.non_conflicting_action_text.lower())

    def test_sensitivity_table_and_filing_reconciliation(self):
        """Tests sensitivity table Gordon slope linearity, share count reconciliation, and CAR 18.9% / Tier-1 17.5%."""
        table = self.ledger.sensitivity_table
        self.assertEqual(table.trailing_roe_pct, 12.84)
        self.assertEqual(table.filing_derived_roe_pct, 12.84)
        self.assertIn("Q2 FY27", table.filing_roe_source)
        self.assertEqual(table.shares_outstanding_bn, 15.39)
        self.assertEqual(table.total_net_worth_cr, 607600.0)
        self.assertEqual(self.ledger.current_pb, 2.07)
        self.assertEqual(table.car_total_crar_pct, 18.9)
        self.assertEqual(table.car_tier1_pct, 17.5)
        self.assertIn("Total CAR 18.9%", table.car_source)
        self.assertIn("Tier-1 17.5%", table.car_source)
        self.assertEqual(len(table.grid), 3) # 3 ROE rows
        for row in table.grid:
            self.assertEqual(len(row), 3) # 3 Ke cols

        # Test Gordon formula linearity: d(P/B)/d(ROE) = 1 / (Ke - g) = constant
        pb_12_84 = table.grid[0][1].justified_pb
        pb_14 = table.grid[1][1].justified_pb
        pb_16 = table.grid[2][1].justified_pb
        slope1 = (pb_14 - pb_12_84) / (14.0 - 12.84)
        slope2 = (pb_16 - pb_14) / (16.0 - 14.0)
        self.assertAlmostEqual(slope1, slope2, places=2,
                               msg=f"Sensitivity table slope not linear: {slope1} != {slope2}")


if __name__ == "__main__":
    unittest.main()
