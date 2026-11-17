"""
Unit tests for Phase 6: Deterministic Risk & Capital Engine.
"""
import unittest

from hdfc_predictor.deterministic_risk import DeterministicRiskEngine, DeterministicTranchePlan
from hdfc_predictor.abstention import AbstentionDecision


class TestPhase6DeterministicRisk(unittest.TestCase):
    def setUp(self):
        self.engine = DeterministicRiskEngine(
            max_concentration=0.15,
            target_volatility=0.20,
            max_drawdown_limit=0.15
        )
        self.wealth = 10000000.0  # ₹1 Crore total portfolio wealth
        self.current_price = 800.0

    def test_opportunity_score_ladder_sizing(self):
        """Tests dynamic tranche step-ladder sizing across different score tiers."""
        # 1. Score < 60 -> 0 shares
        p_hold = self.engine.calculate_tranche(
            bottom_opportunity_score=55,
            current_price=self.current_price,
            portfolio_wealth=self.wealth
        )
        self.assertEqual(p_hold.exact_shares, 0)
        self.assertEqual(p_hold.tranche_label, "HOLD_CASH")

        # 2. Score 65 -> Starter Tranche (15% base)
        p_starter = self.engine.calculate_tranche(
            bottom_opportunity_score=65,
            current_price=self.current_price,
            portfolio_wealth=self.wealth
        )
        self.assertGreater(p_starter.exact_shares, 0)
        self.assertEqual(p_starter.tranche_label, "TRANCHE_1_STARTER")

        # 3. Score 85 -> Deep Value Tranche (40% base)
        p_deep = self.engine.calculate_tranche(
            bottom_opportunity_score=85,
            current_price=self.current_price,
            portfolio_wealth=self.wealth
        )
        self.assertGreater(p_deep.exact_shares, p_starter.exact_shares)
        self.assertEqual(p_deep.tranche_label, "TRANCHE_3_DEEP_VALUE")

    def test_max_single_stock_concentration_cap_15_pct(self):
        """Tests non-negotiable rule: max 15% of total wealth in HDFC Bank."""
        # Existing position is already ₹15,00,000 (15% of ₹1 Crore)
        p_capped = self.engine.calculate_tranche(
            bottom_opportunity_score=95,  # Max conviction
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            current_position_value=1500000.0  # 15% already held
        )
        self.assertTrue(p_capped.is_concentration_capped)
        self.assertEqual(p_capped.exact_shares, 0)
        self.assertEqual(p_capped.exact_cash_amount, 0.0)
        self.assertEqual(p_capped.remaining_headroom_pct, 0.0)

        # Existing position is ₹14,00,000 (14% held -> only ₹1,00,000 headroom left)
        p_headroom = self.engine.calculate_tranche(
            bottom_opportunity_score=95,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            current_position_value=1400000.0
        )
        self.assertFalse(p_headroom.is_concentration_capped)
        self.assertLessEqual(p_headroom.exact_cash_amount, 100000.0)
        self.assertGreater(p_headroom.exact_shares, 0)

    def test_volatility_scaling_formula(self):
        """Tests that elevated realized volatility dampens position size."""
        # Low volatility (15% vs 20% target) -> vol_scale > 1.0
        p_low_vol = self.engine.calculate_tranche(
            bottom_opportunity_score=75,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            realized_vol_20d=0.15
        )
        # High volatility (35% vs 20% target) -> vol_scale < 1.0
        p_high_vol = self.engine.calculate_tranche(
            bottom_opportunity_score=75,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            realized_vol_20d=0.35
        )
        self.assertGreater(p_low_vol.volatility_scale_factor, 1.0)
        self.assertLess(p_high_vol.volatility_scale_factor, 1.0)
        self.assertGreater(p_low_vol.exact_shares, p_high_vol.exact_shares)

    def test_portfolio_drawdown_dampener_and_halt(self):
        """Tests that portfolio-level drawdown dampens and ultimately halts capital deployment."""
        # 1. 10% portfolio drawdown (approaching 15% limit)
        p_dd = self.engine.calculate_tranche(
            bottom_opportunity_score=80,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            current_portfolio_drawdown=0.10
        )
        self.assertLess(p_dd.drawdown_dampener_factor, 1.0)
        self.assertFalse(p_dd.is_drawdown_halted)

        # 2. 16% portfolio drawdown (exceeds 15% limit) -> Hard halt
        p_halt = self.engine.calculate_tranche(
            bottom_opportunity_score=95,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            current_portfolio_drawdown=0.16
        )
        self.assertTrue(p_halt.is_drawdown_halted)
        self.assertEqual(p_halt.exact_shares, 0)
        self.assertEqual(p_halt.drawdown_dampener_factor, 0.0)

    def test_order_parameters_ratchet_and_invalidation(self):
        """Tests limit order window, fundamental invalidation price, and swing-low ratchet rule."""
        plan = self.engine.calculate_tranche(
            bottom_opportunity_score=75,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            atr_14=20.0,
            book_value_per_share=394.84
        )
        self.assertEqual(plan.execution_time_window_days, 5)
        # Entry limit is patient (below current market price)
        self.assertLess(plan.entry_limit_price, self.current_price)
        # Invalidation price based on fundamental crisis P/B (1.50x = ₹592.3)
        self.assertEqual(plan.fundamental_invalidation_price, round(394.84 * 1.50, 1))
        # Ratchet rule explicitly forbids trailing on ATR alone
        self.assertIn("never trail on ATR alone", plan.trailing_ratchet_rule)
        self.assertIn("higher swing low", plan.trailing_ratchet_rule)

    def test_abstention_blocks_risk_deployment(self):
        """Tests that Abstention Engine signals completely block risk deployment."""
        decision = AbstentionDecision(
            should_abstain=True,
            action="ABSTAIN",
            blocking_reasons=["Data quality stale: Market feed delayed > 24 hours"],
            warnings=["High source divergence"],
            severity="CRITICAL"
        )
        plan = self.engine.calculate_tranche(
            bottom_opportunity_score=95,
            current_price=self.current_price,
            portfolio_wealth=self.wealth,
            abstention=decision
        )
        self.assertEqual(plan.exact_shares, 0)
        self.assertEqual(plan.exact_cash_amount, 0.0)
        self.assertEqual(plan.tranche_label, "ABSTAIN_HALT")


if __name__ == "__main__":
    unittest.main()
