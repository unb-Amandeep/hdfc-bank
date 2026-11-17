"""
Unit tests for Earnings Call Transcript & Management Guidance Engine.
"""
import unittest
from hdfc_predictor.earnings_transcript import EarningsTranscriptEngine, EarningsTranscriptReport


class TestEarningsTranscriptEngine(unittest.TestCase):
    def test_report_structure_and_weights(self):
        report = EarningsTranscriptEngine.get_latest_transcript_report()
        self.assertIsInstance(report, EarningsTranscriptReport)
        self.assertEqual(report.fiscal_quarter, "Q2 FY26")
        
        # Verify pillar weights sum to 100%
        total_weight = sum(p.weight_pct for p in report.pillars)
        self.assertAlmostEqual(total_weight, 100.0, places=2)
        
        # Check weighted score is within valid bounds
        self.assertGreaterEqual(report.total_weighted_score, 0.0)
        self.assertLessEqual(report.total_weighted_score, 100.0)
        self.assertEqual(report.total_weighted_score, 81.2)

        # Check key speakers and quotes exist
        self.assertTrue(any("Sashidhar Jagdishan" in p.executive_speaker for p in report.pillars))
        self.assertTrue(any("Srinivasan Vaidyanathan" in p.executive_speaker for p in report.pillars))
        self.assertGreater(len(report.core_strategic_priorities), 0)
        self.assertGreater(len(report.analyst_concerns_raised), 0)
        self.assertGreater(len(report.management_rebuttals), 0)


if __name__ == "__main__":
    unittest.main()
