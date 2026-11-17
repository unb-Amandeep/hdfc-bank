"""
Unit tests for Phase 1: Point-in-Time Data Foundation, Corporate Actions,
ADR Normalization, Data Quality Gates, and Abstention Engine.
"""
import unittest
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from hdfc_predictor.database import (
    init_db,
    log_raw_observation,
    get_point_in_time_observation,
    get_corporate_actions,
    log_data_quality
)
from hdfc_predictor.data_quality import CorporateActionAdjuster, DataQualityGate
from hdfc_predictor.adr_normalizer import ADRNormalizer
from hdfc_predictor.abstention import AbstentionEngine, AbstentionDecision
from hdfc_predictor.capital_allocator import CapitalAllocator


class TestPhase1DataAndAbstention(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def test_01_point_in_time_observations(self):
        """Tests point-in-time observation insertion and as-of retrieval without look-ahead."""
        # Insert historical revisions
        log_raw_observation(
            metric="NIM",
            value=3.40,
            source="Q1 FY25 Report",
            as_of_date="2024-06-30",
            entity_scope="HDFCBANK_STANDALONE",
            filing_timestamp="2024-07-20T10:00:00",
            revision_no=0,
            is_verified=True
        )
        log_raw_observation(
            metric="NIM",
            value=3.16,
            source="Q2 FY27 Form 6-K",
            as_of_date="2026-09-30",
            entity_scope="HDFCBANK_STANDALONE",
            filing_timestamp="2026-10-18T10:00:00",
            revision_no=0,
            is_verified=True
        )

        # Query as of 2025-01-01 (should return 3.40, NOT 3.16 which was filed in 2026)
        obs_past = get_point_in_time_observation("NIM", "HDFCBANK_STANDALONE", "2025-01-01")
        self.assertIsNotNone(obs_past)
        self.assertEqual(obs_past["value"], 3.40)
        self.assertEqual(obs_past["as_of_date"], "2024-06-30")

        # Query as of 2026-11-01 (should return 3.16)
        obs_latest = get_point_in_time_observation("NIM", "HDFCBANK_STANDALONE", "2026-11-01")
        self.assertIsNotNone(obs_latest)
        self.assertEqual(obs_latest["value"], 3.16)

    def test_02_corporate_actions_and_adjustments(self):
        """Tests split adjustments on per-share metrics."""
        actions = get_corporate_actions("HDFCBANK.NS")
        self.assertGreaterEqual(len(actions), 2)

        # Before 2019-09-19 1:2 split, EPS of 50.0 should adjust to 25.0
        adj_eps = CorporateActionAdjuster.adjust_per_share_metric(50.0, "2018-05-01", "HDFCBANK.NS")
        self.assertEqual(adj_eps, 25.0)

        # Post 2019 split, metric is unadjusted factor 1.0
        current_eps = CorporateActionAdjuster.adjust_per_share_metric(45.75, "2026-10-01", "HDFCBANK.NS")
        self.assertEqual(current_eps, 45.75)

    def test_03_adr_normalizer(self):
        """Tests ADR to INR conversion, ratio configurability, and calendar mismatch."""
        normalizer = ADRNormalizer(adr_shares_per_ads=3.0)
        quote = normalizer.normalize(
            adr_usd_price=26.29,
            usd_inr_rate=93.58,
            local_inr_price=814.90,
            us_date="2026-11-16",
            india_date="2026-11-16"
        )
        # Expected: (26.29 * 93.58) / 3 = 820.07
        self.assertAlmostEqual(quote.adr_inr_per_share, 820.07, delta=0.5)
        self.assertGreater(quote.adr_premium_discount_pct, 0.0)
        self.assertFalse(quote.is_calendar_mismatch)

        # Test calendar mismatch flag
        holiday_quote = normalizer.normalize(
            adr_usd_price=26.29,
            usd_inr_rate=93.58,
            local_inr_price=814.90,
            us_date="2026-11-13",
            india_date="2026-11-16"
        )
        self.assertTrue(holiday_quote.is_calendar_mismatch)

    def test_04_data_quality_gates(self):
        """Tests schema validation, freshness, and raw bar indicator recomputation."""
        gate = DataQualityGate("HDFCBANK.NS")

        # Synthetic bars
        np.random.seed(42)
        prices = np.cumprod(1 + np.random.normal(0.001, 0.015, 40)) * 800.0
        df = pd.DataFrame({
            "Open": prices * 0.99,
            "High": prices * 1.01,
            "Low": prices * 0.98,
            "Close": prices,
            "Volume": [20000000] * 40
        })

        # Fresh quote
        quote = {
            "timestamp": datetime.now().isoformat(),
            "current_price": float(prices[-1])
        }

        # Calculate raw RSI
        recomp_ok, metrics, issues = gate.recompute_and_cross_check_indicators(df, {})
        self.assertTrue(recomp_ok)
        self.assertIn("recomputed_rsi_14", metrics)
        self.assertTrue(0 <= metrics["recomputed_rsi_14"] <= 100)

        # Cross check gate with intentionally drifted feature claim
        drifted_features = {"rsi_14": metrics["recomputed_rsi_14"] + 15.0}  # Large discrepancy
        res = gate.run_all_quality_checks(quote, df, drifted_features)
        self.assertFalse(res.passed)
        self.assertTrue(any("RSI check failed" in issue for issue in res.issues))

    def test_05_abstention_engine_and_capital_blocking(self):
        """Verifies that abstention triggers and strictly forces capital allocation to 0%."""
        abstention_engine = AbstentionEngine()
        allocator = CapitalAllocator(default_budget=1000000.0)

        # Case 1: Healthy condition -> Capital proceeds
        fake_quality_pass = type("QualityCheckResult", (), {"passed": True, "status": "PASSED", "issues": []})()
        normal_dec = abstention_engine.evaluate(
            quality_result=fake_quality_pass,
            quote_primary={"current_price": 813.50},
            quote_secondary={"price": 814.00},
            model_confidence=0.65,
            vol_ratio=1.2
        )
        self.assertFalse(normal_dec.should_abstain)
        self.assertEqual(normal_dec.action, "PROCEED")

        normal_plan = allocator.compute_allocation_plan(
            bottom_score=78,
            current_price=813.50,
            abstention=normal_dec
        )
        self.assertEqual(normal_plan.target_cumulative_allocation_pct, 20.0)
        self.assertEqual(normal_plan.proposed_deployment_cash, 200000.0)

        # Case 2: Source conflict -> ABSTAIN triggered & blocks capital allocation
        conflict_dec = abstention_engine.evaluate(
            quality_result=fake_quality_pass,
            quote_primary={"current_price": 813.50},
            quote_secondary={"price": 850.00},  # ~4.5% divergence
            model_confidence=0.65,
            vol_ratio=1.2
        )
        self.assertTrue(conflict_dec.should_abstain)
        self.assertEqual(conflict_dec.action, "ABSTAIN")
        self.assertTrue(any("Cross-source conflict" in r for r in conflict_dec.blocking_reasons))

        blocked_plan = allocator.compute_allocation_plan(
            bottom_score=78,
            current_price=813.50,
            abstention=conflict_dec
        )
        self.assertEqual(blocked_plan.target_cumulative_allocation_pct, 0.0)
        self.assertEqual(blocked_plan.proposed_deployment_cash, 0.0)
        self.assertEqual(blocked_plan.reserve_capital_pct, 100.0)
        self.assertIn("STRICTLY BLOCKED BY ABSTENTION", blocked_plan.allocation_rationale)


if __name__ == "__main__":
    unittest.main()
