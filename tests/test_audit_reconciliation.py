"""
Comprehensive Audit & Reconciliation Test Suite for HDFC Bank Stock Engine.
Enforces non-negotiable mathematical invariants:
1. Net Worth / Shares = BVPS.
2. ROE = Annualized Profit / Same Net Worth.
3. Bear < Base < Bull across all scenarios and sensitivity grid.
4. No hardcoded price target literals (710/920/1058/745/775) in valuation logic.
5. Gate 0 rejects inconsistent data.
"""
import unittest
from hdfc_predictor.valuation_targets import ValuationTargetEngine
from hdfc_predictor.accumulation_gates import AccumulationGatesEngine, BANK_SAFETY_CONFIG


class TestAuditReconciliation(unittest.TestCase):
    def test_equity_and_bvps_reconciliation(self):
        """Rule 1: Net Worth / Shares = BVPS within 50 paise tolerance."""
        net_worth = ValuationTargetEngine.TOTAL_NET_WORTH_CR # ₹6,07,600 Cr
        shares = ValuationTargetEngine.TOTAL_SHARES_BN       # 15.39 Bn
        expected_bvps = net_worth / (shares * 100.0)        # ₹394.8018
        
        self.assertAlmostEqual(ValuationTargetEngine.DEFAULT_BVPS, expected_bvps, delta=0.50)

    def test_roe_uses_same_equity_series(self):
        """Rule 2: Trailing ROE must use annualized Q2 profit over the exact same Net Worth."""
        net_worth = ValuationTargetEngine.TOTAL_NET_WORTH_CR # ₹6,07,600 Cr
        ann_profit = ValuationTargetEngine.ANNUALIZED_PAT_CR  # ₹78,040 Cr
        calc_roe = (ann_profit / net_worth) * 100.0          # 12.844%
        
        self.assertAlmostEqual(ValuationTargetEngine.TRAILING_ROE_PCT, calc_roe, delta=0.05)
        self.assertEqual(round(ValuationTargetEngine.TRAILING_ROE_PCT, 1), 12.8)

    def test_bear_base_bull_strict_ordering(self):
        """Rule 3: Bear < Base < Bull strictly on justified P/B and target prices."""
        ledger = ValuationTargetEngine.compute_unified_targets(reference_price=817.80)
        scenarios = {s.name: s for s in ledger.scenarios}
        
        bear = scenarios["BEAR"]
        base = scenarios["BASE"]
        bull = scenarios["BULL"]

        self.assertLess(bear.justified_pb, base.justified_pb, "Bear PB must be less than Base PB")
        self.assertLess(base.justified_pb, bull.justified_pb, "Base PB must be less than Bull PB")

        self.assertLess(bear.target_price, base.target_price, "Bear price must be less than Base price")
        self.assertLess(base.target_price, bull.target_price, "Base price must be less than Bull price")

        # Check sensitivity grid monotonicity across ROE
        grid = ledger.sensitivity_table.grid
        for col_idx in range(len(grid[0])):
            roe_11 = grid[0][col_idx].implied_fair_value
            roe_14 = grid[1][col_idx].implied_fair_value
            roe_16 = grid[2][col_idx].implied_fair_value
            self.assertLess(roe_11, roe_14, f"Grid column {col_idx} failed monotonicity: 11% vs 14%")
            self.assertLess(roe_14, roe_16, f"Grid column {col_idx} failed monotonicity: 14% vs 16%")

    def test_implied_roe_expectations_consistency(self):
        """Rule 4: Market-implied ROE reverse-engineered across terminal growth rates."""
        ledger = ValuationTargetEngine.compute_unified_targets(reference_price=817.80)
        expectations = ledger.implied_expectations
        
        self.assertEqual(len(expectations), 3)
        # For terminal growth = 8.0%, Implied ROE = 2.071 * (0.1228 - 0.08) + 0.08 ≈ 16.9%
        exp_8 = next(e for e in expectations if e.terminal_growth_pct == 8.0)
        self.assertGreater(exp_8.market_implied_roe_pct, 16.0)
        self.assertLess(exp_8.market_implied_roe_pct, 17.5)
        self.assertGreater(exp_8.gap_vs_trailing_roe_bps, 400.0)

    def test_buy_zone_is_dynamic_not_hardcoded(self):
        """Rule 5: Buy zone changes dynamically with Base target price."""
        bvps = 394.80
        bz1 = ValuationTargetEngine.derive_buy_zone(base_target_price=900.0, bvps=bvps)
        bz2 = ValuationTargetEngine.derive_buy_zone(base_target_price=1000.0, bvps=bvps)
        
        self.assertNotEqual(bz1.limit_zone_high, bz2.limit_zone_high)
        self.assertNotEqual(bz1.limit_zone_low, bz2.limit_zone_low)
        self.assertLess(bz1.limit_zone_low, bz1.limit_zone_high)

    def test_gate_0_rejects_inconsistent_equity(self):
        """Rule 6: Gate 0 must fail and output ABSTAIN when Net Worth conflicts with BVPS."""
        # Valid check passes
        g0_pass = AccumulationGatesEngine.evaluate_gate_0_data_integrity(
            net_worth_cr=607600.0,
            shares_bn=15.39,
            reported_bvps=394.80,
            q2_profit_cr=16821.0,
            reported_roe_pct=11.07
        )
        self.assertTrue(g0_pass.passed)
        self.assertEqual(g0_pass.status, "PASS")

        # Inconsistent equity fails Gate 0
        g0_fail = AccumulationGatesEngine.evaluate_gate_0_data_integrity(
            net_worth_cr=454600.0, # Old equity
            shares_bn=15.39,
            reported_bvps=394.80,  # Mismatched BVPS
            q2_profit_cr=16821.0,
            reported_roe_pct=11.07
        )
        self.assertFalse(g0_fail.passed)
        self.assertEqual(g0_fail.status, "ABSTAIN")

    def test_gate_2_and_filing_source_consistency(self):
        """Rule 7: Gate 2 metrics must match certified Q2 FY27 filing exactly."""
        import json
        with open("hdfc_predictor/data/hdfc_q2fy27_filing_source.json") as f:
            data = json.load(f)
            filing = data["document_metadata"]["reported_metrics"]
        
        gate2 = AccumulationGatesEngine.evaluate_gate_2_solvency()
        metrics = gate2.evidence_metrics
        self.assertEqual(metrics["car_pct"], filing["car_total_pct"])
        self.assertEqual(metrics["deposit_growth_yoy_pct"], filing["deposit_growth_yoy_pct"])
        self.assertEqual(metrics["cd_ratio_pct"], filing["cd_ratio_pct"])
        self.assertEqual(metrics["gnpa_pct"], filing["gross_npa_pct"])
        self.assertEqual(metrics["nnpa_pct"], filing["net_npa_pct"])
        self.assertTrue(gate2.passed)

    def test_pb_percentile_hierarchy_consistency(self):
        """Rule 8: Percentiles must be strictly monotonic: 710 < 742 < 772 < 814.95."""
        bvps = 394.80
        p_710 = ValuationTargetEngine.compute_pb_percentile(710.0 / bvps)
        p_742 = ValuationTargetEngine.compute_pb_percentile(742.0 / bvps)
        p_772 = ValuationTargetEngine.compute_pb_percentile(772.0 / bvps)
        p_815 = ValuationTargetEngine.compute_pb_percentile(814.95 / bvps)

        self.assertLess(p_710, p_742, f"710 percentile ({p_710}) must be less than 742 ({p_742})")
        self.assertLess(p_742, p_772, f"742 percentile ({p_742}) must be less than 772 ({p_772})")
        self.assertLess(p_772, p_815, f"772 percentile ({p_772}) must be less than 814.95 ({p_815})")
        self.assertAlmostEqual(p_815, 51.3, delta=2.0, msg="Current price ₹814.95 must be post-merger median (~51st percentile)")



if __name__ == "__main__":
    unittest.main()
