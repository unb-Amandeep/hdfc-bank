"""
Unit tests for Management Promise & Guidance Tracker Engine.
"""
import unittest
from hdfc_predictor.earnings_transcript import EarningsTranscriptEngine, PromiseTrackerReport


class TestEarningsTranscriptEngine(unittest.TestCase):
    def test_promise_tracker_verbatim_string_match(self):
        report = EarningsTranscriptEngine.get_latest_transcript_report()
        self.assertIsInstance(report, PromiseTrackerReport)
        self.assertTrue(report.is_source_loaded)
        self.assertEqual(report.fiscal_period, "Q2 FY27")
        self.assertGreater(report.total_promises_tracked, 0)
        
        # Verify every promise passed strict string matching in the source file
        for p in report.promises:
            self.assertTrue(p.verification_check_passed, f"Promise {p.promise_id} failed verbatim check")
            self.assertIn(p.delivery_status, ["DELIVERED", "IN PROGRESS", "BREACHED"])
            self.assertNotEqual(p.latest_actual_value, "Not available")

    def test_missing_source_file_graceful_handling(self):
        # Temporarily test path not found behavior
        original_path = EarningsTranscriptEngine.SOURCE_FILE
        from pathlib import Path
        EarningsTranscriptEngine.SOURCE_FILE = Path("/tmp/non_existent_filing_source.json")
        try:
            report = EarningsTranscriptEngine.get_latest_transcript_report()
            self.assertFalse(report.is_source_loaded)
            self.assertEqual(report.document_name, "No source loaded")
        finally:
            EarningsTranscriptEngine.SOURCE_FILE = original_path


if __name__ == "__main__":
    unittest.main()
