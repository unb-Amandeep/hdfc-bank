"""
Unit Tests for Historical Analogue Engine Dynamic Calculations.
Fails if:
1. Header metrics disagree with table rows.
2. Any historical episode shows 'In Progress' / None.
3. Clustered episodes within 6 months are not flagged.
4. Pre-merger vs post-merger regime is missing.
5. Trigger rule check is not executed.
"""
import unittest
import numpy as np

from hdfc_predictor.historical_analogues import HistoricalAnalogueEngine


class TestHistoricalAnaloguesDynamic(unittest.TestCase):
    def setUp(self):
        self.report = HistoricalAnalogueEngine.get_full_analogue_report(current_price=817.80, current_pb=2.06)
        self.episodes = self.report.all_episodes

    def test_header_metrics_dynamically_match_rows(self):
        """Tests that all summary stats are calculated directly from rows."""
        total = len(self.episodes)
        self.assertEqual(self.report.total_episodes, total)

        expected_winners = sum(1 for e in self.episodes if e.outcome_status_6m == "WINNER")
        expected_losers = sum(1 for e in self.episodes if e.outcome_status_6m == "LOSER")
        expected_choppy = sum(1 for e in self.episodes if e.outcome_status_6m == "CHOPPY")

        self.assertEqual(self.report.winning_episodes_6m, expected_winners)
        self.assertEqual(self.report.losing_episodes_6m, expected_losers)
        self.assertEqual(self.report.choppy_episodes_6m, expected_choppy)

        expected_hit_rate = round((expected_winners / total) * 100, 1)
        self.assertEqual(self.report.hit_rate_6m_pct, expected_hit_rate)

        expected_avg_6m = round(float(np.mean([e.actual_return_180d_pct for e in self.episodes])), 1)
        self.assertEqual(self.report.avg_return_6m_pct, expected_avg_6m)

    def test_no_episode_shows_in_progress(self):
        """Tests that all historical episodes older than 1 year have matured 1-year returns."""
        for ep in self.episodes:
            self.assertIsNotNone(
                ep.actual_return_365d_pct,
                f"Episode {ep.cycle_name} has None for 365d return ('In Progress')!"
            )
            self.assertIsInstance(ep.actual_return_365d_pct, float)

    def test_clustering_and_regimes_tagged(self):
        """Tests that episodes within 6 months are flagged and regimes are categorized."""
        clustered = [e for e in self.episodes if e.is_clustered]
        self.assertGreaterEqual(len(clustered), 2, "Expected at least 2 clustered episodes (< 6M retest)")

        pre_merger = [e for e in self.episodes if e.regime_era == "PRE_MERGER"]
        post_merger = [e for e in self.episodes if e.regime_era == "POST_MERGER"]
        self.assertGreater(len(pre_merger), 0)
        self.assertGreater(len(post_merger), 0)
        self.assertEqual(len(pre_merger) + len(post_merger), len(self.episodes))

    def test_trigger_rule_stated_and_evaluated(self):
        """Tests trigger rule specification and evaluation for today."""
        rule = self.report.trigger_rule
        self.assertFalse(rule.today_meets_rule, "Today at ₹817.80 should NOT trigger immediate buy; waiting for limit pullback.")
        self.assertIn("P/B <= 2.40x", rule.valuation_threshold_post_merger)
        self.assertIn("745", rule.pullback_requirement)

    def test_small_sample_confidence_interval(self):
        """Tests that small sample disclaimer with 95% CI is reported."""
        ci_str = self.report.sample_size_confidence_interval
        self.assertIn("Small sample, n=8", ci_str)
        self.assertIn("95% CI", ci_str)


if __name__ == "__main__":
    unittest.main()
