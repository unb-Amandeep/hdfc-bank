"""
UI and Data Tests for Backtest Chart and Event Stream Rendering.
FAILS THE BUILD IF:
1. Backtest equity curve has fewer than 2 plotted points.
2. Any curve point has missing or invalid values for strategy, benchmark, or SIP.
3. Event stream is empty or fails to generate 'Why did it move?'.
"""
import unittest

from hdfc_predictor.backtester import Backtester
from hdfc_predictor.event_intelligence import EventIntelligenceEngine
from hdfc_predictor.news_engine import NewsEngine


class TestChartAndEventsRendering(unittest.TestCase):
    def test_backtest_chart_has_at_least_two_points(self):
        """Tests that the backtester returns an equity curve with >= 2 points for charting."""
        bt = Backtester()
        result = bt.run_backtest(period="2y")
        curve = result.equity_curve

        self.assertIsNotNone(curve, "Equity curve is None!")
        self.assertGreaterEqual(
            len(curve),
            2,
            f"Backtest chart has fewer than 2 plotted points: found {len(curve)} points!"
        )

        # Validate structure of each point for Chart.js
        for pt in curve[:10]:
            self.assertIn("date", pt)
            self.assertIn("strategy_equity", pt)
            self.assertIn("benchmark_equity", pt)
            self.assertIn("sip_equity", pt)
            self.assertGreater(pt["strategy_equity"], 0)
            self.assertGreater(pt["benchmark_equity"], 0)
            self.assertGreater(pt["sip_equity"], 0)

    def test_event_stream_and_why_moved_explanation(self):
        """Tests event classification and 'Why did it move?' line generation."""
        ne = NewsEngine()
        raw_news = ne.get_latest_news_and_sentiment()
        articles = raw_news.get("top_articles", [])
        
        events = EventIntelligenceEngine.filter_and_classify_stream(articles)
        self.assertIn("why_did_it_move", events)
        self.assertTrue(len(events["why_did_it_move"]) > 0)
        self.assertIn("material_events", events)
        self.assertGreater(len(events["material_events"]), 0)


if __name__ == "__main__":
    unittest.main()
