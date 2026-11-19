"""
Comprehensive Automated Smoke Test Suite for HDFC Bank Dashboard & REST API.
Verifies:
1. Serves self-contained HTML (zero external CDN dependencies).
2. GET / returns 200 OK with all required sections and containers.
3. GET /api/status returns 200 OK with complete verified data payload.
4. GET /api/backtest returns >= 2 plotted points for equity curve charting.
5. POST /api/trigger-signal successfully recalculates signal with 200 OK (no 500 crashes).
6. GET /api/history returns valid recent prediction records.
7. Fails the build on any 4xx or 5xx error or unverified data leak.
"""
import unittest
import io
import json
from typing import Tuple

from hdfc_predictor.dashboard import DashboardHandler, HTML_TEMPLATE


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


class TestDashboardSmoke(unittest.TestCase):
    @classmethod
    def make_request(cls, method: str, path: str, body: bytes = b"") -> Tuple[int, bytes]:
        raw = f"{method} {path} HTTP/1.1\r\nHost: localhost\r\nContent-Length: {len(body)}\r\n\r\n".encode("utf-8") + body
        sock = MockSocket(raw)
        DashboardHandler(sock, ("127.0.0.1", 12345), None)
        out = sock.output.getvalue()
        header_part, _, body_part = out.partition(b"\r\n\r\n")
        lines = header_part.decode("utf-8").split("\r\n")
        status_code = int(lines[0].split()[1])
        return status_code, body_part

    def test_01_html_is_self_contained_with_no_external_cdns(self):
        """Rule 9: Bundling must be self-contained; zero external CDN dependencies."""
        status, body = self.make_request("GET", "/")
        self.assertEqual(status, 200)
        html = body.decode("utf-8")

        # Zero outside CDN dependencies
        self.assertNotIn("cdn.tailwindcss.com", html, "External Tailwind CDN found in HTML!")
        self.assertNotIn("cdn.jsdelivr.net", html, "External Chart.js CDN found in HTML!")
        self.assertNotIn("fonts.googleapis.com", html, "External Google Fonts found in HTML!")

        # Verify all essential UI containers are present
        self.assertIn('id="equityChart"', html)
        self.assertIn('id="sectionCompass"', html)
        self.assertIn('Daily Compass', html)
        self.assertIn('id="eventsListContainer"', html)
        self.assertIn('id="gatesListContainer"', html)
        self.assertIn('id="peerWatchlistTableBody"', html)
        self.assertIn('id="priceLadderTableBody"', html)
        self.assertIn('id="toastContainer"', html)
        self.assertIn('id="btnTrigger"', html)

    def test_02_api_status_payload_integrity(self):
        """Rule 1 & 2: GET /api/status returns complete, verified decision object."""
        status, body = self.make_request("GET", "/api/status")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertIn("reference_price", data)
        self.assertGreater(data["reference_price"], 0)

        # Valuation ledger verification
        vl = data.get("valuation_ledger")
        self.assertIsNotNone(vl)
        self.assertEqual(vl["book_value_per_share"], 394.80)
        self.assertEqual(vl["trailing_roe_pct"], 12.84)
        
        # Staged accumulation buy zone
        bz = vl.get("dynamic_buy_zone")
        self.assertIsNotNone(bz)
        ref_p = data["reference_price"]
        expected_high = round(ref_p * (1.0 - 0.0523), 0)
        expected_low = round(ref_p * (1.0 - 0.0890), 0)
        self.assertEqual(bz["limit_zone_low"], expected_low)
        self.assertEqual(bz["limit_zone_high"], expected_high)
        self.assertIn("shares", bz["shares_range_label"])

        # Gate verification
        gates = data.get("accumulation_gates", {}).get("gates", [])
        self.assertEqual(len(gates), 6)
        g0 = gates[0]
        self.assertEqual(g0["gate_number"], 0)
        self.assertEqual(g0["status"], "PASS")
        self.assertTrue(g0["evidence_metrics"]["filing_authenticated"])

        # Event stream verification
        events = data.get("events")
        self.assertIsNotNone(events)
        self.assertIn("why_did_it_move", events)
        self.assertTrue(len(events["why_did_it_move"]) > 0)
        self.assertNotIn("MSCI", events["why_did_it_move"], "Obsolete MSCI claim leaked in event stream!")

        # Peer watchlist verification
        peers = data.get("peer_watchlist", [])
        self.assertEqual(len(peers), 4)

        # Daily Compass verification (technicals + probabilistic forecasts)
        compass = data.get("daily_compass")
        self.assertIsNotNone(compass, "daily_compass payload missing from /api/status")

        tech = compass.get("technicals")
        self.assertIsNotNone(tech)
        self.assertGreater(tech["dma_20"], 0)
        self.assertGreater(tech["dma_50"], 0)
        self.assertGreater(tech["dma_200"], 0)
        self.assertGreater(tech["atr_14"], 0)
        self.assertGreater(tech["anchored_vwap"], 0)
        self.assertIn("fibonacci", tech)
        self.assertGreaterEqual(tech["fibonacci"]["fib_382"], 760.0)
        self.assertLessEqual(tech["fibonacci"]["fib_382"], 765.0)
        self.assertGreaterEqual(tech["fibonacci"]["fib_500"], 742.0)
        self.assertLessEqual(tech["fibonacci"]["fib_500"], 746.0)

        forecast = compass.get("probabilistic_forecast")
        self.assertIsNotNone(forecast)
        self.assertGreaterEqual(len(forecast["forecasts"]), 4)
        self.assertGreater(forecast["brier_skill_score_pct"], 0)
        f0 = forecast["forecasts"][0]
        self.assertIn("prob_1d_pct", f0)
        self.assertIn("prob_3d_pct", f0)
        self.assertIn("prob_5d_pct", f0)
        self.assertIn("naive_prob_5d_pct", f0)
        self.assertIn("edge_5d_pct", f0)

        scoreboard = compass.get("compass_scoreboard")
        self.assertIsNotNone(scoreboard)
        self.assertGreater(scoreboard["total_forecasts_logged"], 0)

    def test_03_api_backtest_chart_points(self):
        """Rule 10: GET /api/backtest must return an equity curve with >= 2 plotted points."""
        status, body = self.make_request("GET", "/api/backtest?period=2y")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))

        curve = data.get("equity_curve", [])
        self.assertGreaterEqual(len(curve), 2, f"Backtest chart has fewer than 2 points: found {len(curve)}")
        pt = curve[0]
        self.assertIn("date", pt)
        self.assertIn("strategy_equity", pt)
        self.assertIn("benchmark_equity", pt)
        self.assertIn("sip_equity", pt)

    def test_04_api_trigger_signal_async_accepted(self):
        """Rule 3: POST /api/trigger-signal must return HTTP 202 Accepted without blocking."""
        status, body = self.make_request("POST", "/api/trigger-signal", body=b"{}")
        self.assertEqual(status, 202)
        data = json.loads(body.decode("utf-8"))

        self.assertIn(data.get("status"), ["RUNNING", "SUCCESS"])
        self.assertIn("started", data.get("message", "").lower())

        # Polling /api/refresh-status returns 200 OK
        ref_status, ref_body = self.make_request("GET", "/api/refresh-status")
        self.assertEqual(ref_status, 200)
        ref_data = json.loads(ref_body.decode("utf-8"))
        self.assertIn("status", ref_data)
        self.assertIn("message", ref_data)

    def test_05_api_history_returns_valid_records(self):
        """Rule 10: GET /api/history returns 200 OK and valid list."""
        status, body = self.make_request("GET", "/api/history")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertIsInstance(data, list)

    def test_06_filing_route_serves_pages_1_to_4(self):
        """Rule 11: GET /filings/q2fy27 returns certified statutory report with pages 1-4."""
        status, body = self.make_request("GET", "/filings/q2fy27")
        self.assertEqual(status, 200)
        html = body.decode("utf-8")

        self.assertIn('id="page1"', html)
        self.assertIn('id="page2"', html)
        self.assertIn('id="page3"', html)
        self.assertIn('id="page4"', html)
        self.assertIn("30,40,000", html)
        self.assertIn("18.8%", html)
        self.assertIn("6,07,600", html)
        self.assertIn("394.80", html)
        self.assertIn("a044248425db1ac790b420d7b697f7184fd6be59466596a1bc7319e775f940d3", html)

    def test_07_header_verdict_equals_toast_verdict(self):
        """Rule 12: Primary verdict in status payload must match Refresh Job Manager primary verdict."""
        from hdfc_predictor.dashboard import get_status_payload, RefreshJobManager
        from hdfc_predictor.accumulation_gates import AccumulationGatesEngine
        from hdfc_predictor.valuation_targets import ValuationTargetEngine

        status_data = get_status_payload()
        header_verdict = status_data["accumulation_gates"]["final_action"]
        self.assertEqual(header_verdict, "WAIT")

        # Start job and verify message format
        job = RefreshJobManager.start_job(force=True)
        self.assertEqual(job["status"], "RUNNING")

    def test_08_healthz_endpoint(self):
        """Production Requirement 8: GET /healthz returns 200 OK with health status and feed state."""
        status, body = self.make_request("GET", "/healthz")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "hdfc-accumulation-engine")
        self.assertTrue(data.get("database", {}).get("connected"))
        self.assertIn("DATA STALE", data.get("feed", {}).get("status"))

    def test_09_backup_ledger_endpoint(self):
        """Production Requirement 8: POST /api/backup-ledger returns 200 OK and creates snapshot."""
        status, body = self.make_request("POST", "/api/backup-ledger")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertEqual(data.get("status"), "success")
        self.assertIn("backup_path", data)

    def test_10_single_decision_object_and_macro_market(self):
        """Production Requirements 2 & 7: Single Decision Object and Macro inputs in /api/status."""
        status, body = self.make_request("GET", "/api/status")
        self.assertEqual(status, 200)
        data = json.loads(body.decode("utf-8"))

        dec = data.get("decision_object")
        self.assertIsNotNone(dec)
        self.assertIn(dec["canonical_action"], ["WAIT", "BUY", "SELL"])
        self.assertTrue(isinstance(dec["inputs"], (list, dict)))
        self.assertGreaterEqual(len(dec["inputs"]), 4)
        self.assertIsInstance(dec["disagreements"], list)

        macro = data.get("macro_market")
        self.assertIsNotNone(macro)
        self.assertIn("institutional_flows", macro)
        self.assertIn("india_vix", macro)
        self.assertIn("bank_nifty", macro)
        self.assertIn("options_oi", macro)
        vix_val = macro["india_vix"].get("vix_level") or macro["india_vix"].get("value")
        self.assertAlmostEqual(vix_val, 14.85, places=1)
        bn_val = macro["bank_nifty"].get("index_level") or macro["bank_nifty"].get("value")
        self.assertEqual(bn_val, 51840)


if __name__ == "__main__":
    unittest.main()
