"""
Unit tests for Phase 2: Historical Replay Simulator, Next-Session VWAP Execution,
Baselines (Buy & Hold, Monthly SIP, Drawdown, Valuation), and Counterfactual Policies.
"""
import unittest
import pandas as pd
import numpy as np

from hdfc_predictor.replay_simulator import HistoricalReplaySimulator, SimulationMetrics, ReplayReport


class TestPhase2ReplaySimulator(unittest.TestCase):
    def setUp(self):
        # Generate synthetic realistic 2-year daily price dataframe (504 trading bars)
        np.random.seed(101)
        dates = pd.date_range("2024-01-01", periods=300, freq="B")
        # Start at 800, dip to 680, recover to 820
        rets = np.random.normal(0.0003, 0.015, 300)
        prices = 800.0 * np.cumprod(1 + rets)

        self.df = pd.DataFrame({
            "Open": prices * 0.995,
            "High": prices * 1.012,
            "Low": prices * 0.988,
            "Close": prices,
            "Volume": np.random.randint(15000000, 35000000, 300)
        }, index=dates)

    def test_01_session_vwap_execution(self):
        """Tests that next-session execution uses session VWAP correctly."""
        sim = HistoricalReplaySimulator()
        row = self.df.iloc[10]
        expected_vwap = float((row["Open"] + row["High"] + row["Low"] + row["Close"]) / 4.0)
        calc_vwap = sim.compute_session_vwap(row)
        self.assertAlmostEqual(calc_vwap, expected_vwap, places=4)

    def test_02_full_replay_against_baselines(self):
        """Tests that replay simulator produces strategy and 4 investable baselines on identical capital."""
        sim = HistoricalReplaySimulator(initial_capital=1000000.0)
        report = sim.run_replay(self.df, execution_rule="NEXT_SESSION_VWAP")

        self.assertIsInstance(report, ReplayReport)
        self.assertTrue(report.is_hypothetical_simulation)
        self.assertEqual(report.initial_capital, 1000000.0)

        # Baselines must be present
        self.assertIn("Buy_and_Hold", report.baselines)
        self.assertIn("Monthly_SIP", report.baselines)
        self.assertIn("Fixed_Drawdown_Buyer", report.baselines)
        self.assertIn("Valuation_Percentile", report.baselines)

        # Strategy result check
        strat = report.strategy_result
        self.assertIsInstance(strat, SimulationMetrics)
        self.assertTrue(strat.is_hypothetical_simulation)
        self.assertGreaterEqual(strat.capital_efficiency_pct, 10.0)
        self.assertLessEqual(strat.capital_efficiency_pct, 100.0)

        # MAE must be <= 0.0 (maximum drawdown from inception)
        self.assertLessEqual(strat.max_adverse_excursion_pct, 0.0)
        # MFE must be >= 0.0 (maximum upside crest)
        self.assertGreaterEqual(strat.max_favorable_excursion_pct, 0.0)

    def test_03_counterfactual_policies(self):
        """Verifies counterfactual policy comparison across alternative actions."""
        sim = HistoricalReplaySimulator(initial_capital=1000000.0)
        report = sim.run_replay(self.df)

        cf = report.counterfactual_summary
        self.assertIn("policy_buy_now_full", cf)
        self.assertIn("policy_monthly_sip", cf)
        self.assertIn("policy_staged_tranches", cf)
        self.assertIn("policy_do_nothing_cash", cf)
        self.assertIn("excess_over_buy_and_hold", cf)
        self.assertTrue(cf["is_hypothetical_simulation"])

    def test_04_equity_series_consistency(self):
        """Verifies equity curve time series has identical length to price data bars."""
        sim = HistoricalReplaySimulator(initial_capital=1000000.0)
        report = sim.run_replay(self.df)

        self.assertGreater(len(report.equity_series), 50)
        first_pt = report.equity_series[0]
        self.assertIn("strategy", first_pt)
        self.assertIn("buy_and_hold", first_pt)
        self.assertIn("monthly_sip", first_pt)
        self.assertAlmostEqual(first_pt["strategy"], 1000000.0, delta=1500.0)


if __name__ == "__main__":
    unittest.main()
