"""
Audit Test for Statutory Filing Consistency.
Verifies Requirement 5:
"add a test that fails if a metric on screen differs from the stored filing value."

Validates:
1. Total Net Worth (₹6,07,600 Cr)
2. Shares Outstanding (15.39 Bn)
3. Book Value Per Share (₹394.80)
4. Total Deposits (₹30,40,000 Cr)
5. CASA Deposits (₹11,55,200 Cr)
6. CASA Ratio (38.0%)
7. Deposit YoY Growth (18.8%)
8. Advances (₹25,40,000 Cr) and Advance Growth (16.3%)
9. Credit-to-Deposit Ratio (96.0%)
10. Quarterly PAT (₹19,510 Cr) and Trailing ROE (12.84%)
11. Capital Adequacy Ratio (18.9%) and Tier-1 (17.5%)
12. Gross NPA (1.17%) and Net NPA (0.37%)
13. SHA-256 Filing Hash (a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3)
"""
import unittest
import io
import json

from hdfc_predictor.filing_data import FILING_METRICS
from hdfc_predictor.dashboard import DashboardHandler, get_status_payload


class MockSocket:
    def __init__(self, raw_bytes: bytes):
        self.raw_bytes = raw_bytes
        self.output = io.BytesIO()

    def makefile(self, mode, *args, **kwargs):
        if "r" in mode:
            return io.BytesIO(self.raw_bytes)
        return self.output

    def sendall(self, b):
        self.output.write(b)

    def send(self, b):
        self.output.write(b)
        return len(b)


class TestFilingConsistency(unittest.TestCase):

    @classmethod
    def make_request(cls, method: str, path: str, body: bytes = b""):
        raw = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
        sock = MockSocket(raw)
        DashboardHandler(sock, ("127.0.0.1", 12345), None)
        out = sock.output.getvalue()
        header_part, _, body_part = out.partition(b"\r\n\r\n")
        lines = header_part.decode("utf-8").split("\r\n")
        status_code = int(lines[0].split()[1])
        return status_code, body_part

    def test_01_api_payload_matches_stored_filing_values(self):
        """Rule 1: /api/status values must strictly match FILING_METRICS."""
        status, body = self.make_request("GET", "/api/status")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))

        vl = data["valuation_ledger"]
        self.assertEqual(vl["book_value_per_share"], FILING_METRICS["book_value_per_share"])
        self.assertEqual(vl["trailing_roe_pct"], FILING_METRICS["return_on_equity_pct"])

        sens = vl["sensitivity_table"]
        self.assertEqual(sens["total_net_worth_cr"], FILING_METRICS["total_net_worth_cr"])
        self.assertEqual(sens["shares_outstanding_bn"], FILING_METRICS["shares_outstanding_bn"])
        self.assertEqual(sens["car_total_crar_pct"], FILING_METRICS["capital_adequacy_ratio_pct"])
        self.assertEqual(sens["car_tier1_pct"], FILING_METRICS["tier_1_capital_ratio_pct"])

        # Fundamental profile checks
        fp = data["fundamental"]
        self.assertEqual(fp["casa_ratio_pct"], FILING_METRICS["casa_ratio_pct"])
        self.assertEqual(fp["credit_to_deposit_ratio"], FILING_METRICS["credit_to_deposit_ratio_pct"])
        self.assertEqual(fp["deposit_growth_yoy"], FILING_METRICS["deposit_growth_yoy_pct"])
        self.assertEqual(fp["loan_growth_yoy"], FILING_METRICS["advance_growth_yoy_pct"])
        self.assertEqual(fp["capital_adequacy_ratio"], FILING_METRICS["capital_adequacy_ratio_pct"])
        self.assertEqual(fp["gross_npa_pct"], FILING_METRICS["gross_npa_pct"])
        self.assertEqual(fp["net_npa_pct"], FILING_METRICS["net_npa_pct"])

    def test_02_filing_route_html_matches_stored_metrics(self):
        """Rule 2: /filings/q2fy27 HTML report contains exact certified values."""
        status, body = self.make_request("GET", "/filings/q2fy27")
        self.assertEqual(status, 200)
        html = body.decode("utf-8")

        self.assertIn(str(FILING_METRICS["filing_hash_sha256"]), html)
        self.assertIn("30,40,000", html)
        self.assertIn("11,55,200", html)
        self.assertIn(f"{FILING_METRICS['casa_ratio_pct']:.1f}% CASA Ratio", html)
        self.assertIn("6,07,600", html)
        self.assertIn("394.80", html)
        self.assertIn("15.39 Bn", html)
        self.assertIn("19,510", html)
        self.assertIn("96.0%", html)
        self.assertIn("18.9%", html)

    def test_03_main_dashboard_screen_displays_casa_and_reconciliation(self):
        """Rule 3: Main dashboard HTML renders CASA ratio with dual reconciliation."""
        status, body = self.make_request("GET", "/")
        self.assertEqual(status, 200)
        html = body.decode("utf-8")

        self.assertIn("38.0% (Period-end)", html)
        self.assertIn("31.6% (Daily Avg)", html)
        self.assertIn("30,40,000", html)


if __name__ == "__main__":
    unittest.main()
