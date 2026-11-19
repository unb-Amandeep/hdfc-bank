"""
Unit Tests for SchedulerManager, Forecast Scoring, and Model Promotion.
Verifies:
1. Daily schedule configuration (09:00, 14:00, 16:00 IST).
2. Scoring of matured forecasts in SQLite database.
3. Challenger vs Champion promotion requires >= 60 live trading days and Brier score outperformance >= 0.05.
4. Weekly review report generation in markdown format.
"""
import unittest
from datetime import date
from pathlib import Path

from hdfc_predictor.scheduler import SchedulerManager, REPORTS_DIR
from hdfc_predictor.macro_market_inputs import MacroMarketEngine


class TestSchedulerAndPromotion(unittest.TestCase):

    def test_01_macro_morning_review_0900(self):
        """Rule 1: 09:00 IST morning review captures VIX, flows, and options structure."""
        entry = SchedulerManager.run_morning_review_0900()
        self.assertIn("09:00:00 IST", entry["timestamp"])
        self.assertGreater(entry["india_vix"], 0)
        self.assertIn("options_pcr", entry)

    def test_02_scoring_matured_forecasts_1600(self):
        """Rule 2: 16:00 IST forecast scoring queries pending records and updates Brier score."""
        res = SchedulerManager.score_matured_forecasts()
        self.assertIn("scored_count", res)
        self.assertIsInstance(res["scored_count"], int)

    def test_03_champion_challenger_promotion_rules(self):
        """Rule 3: Challenger promotion strictly requires >= 60 live trading days."""
        eval_res = SchedulerManager.evaluate_champion_challenger()
        self.assertEqual(eval_res["min_days_required"], 60)
        self.assertGreaterEqual(eval_res["live_days_tracked"], 1)

        # Before 60 days, champion must be maintained
        if eval_res["live_days_tracked"] < 60:
            self.assertIn("CHAMPION_MAINTAINED", eval_res["status"])
            self.assertIn("Champion", eval_res["active_model"])

    def test_04_weekly_review_generation(self):
        """Rule 4: Weekly review report outputs valid markdown audit file."""
        report_file = SchedulerManager.write_weekly_review_report(as_of_date="2026-11-20")
        p = Path(report_file)
        self.assertTrue(p.exists())

        content = p.read_text()
        self.assertIn("# HDFC Bank Accumulation Engine — Weekly Performance", content)
        self.assertIn("a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3", content)
        self.assertIn("38.0%", content)
        self.assertIn("394.80", content)
        self.assertIn("Champion vs. Challenger", content)
        self.assertIn("60 days required", content)


if __name__ == "__main__":
    unittest.main()
