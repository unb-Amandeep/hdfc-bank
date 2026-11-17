"""
Unit tests for Phase 7: One Unified Feedback Loop, Immutable Hash Chain, and Champion/Challenger Learning.
"""
import unittest
import sqlite3
import json

from hdfc_predictor.config import settings
from hdfc_predictor.database import (
    init_db,
    get_db_connection,
    insert_immutable_decision,
    verify_decision_chain_integrity,
    get_latest_decision
)
from hdfc_predictor.unified_feedback import (
    UnifiedScheduleManager,
    UnifiedLearningManager,
    AblationStudyEngine,
    ChallengerEvaluationResult
)


class TestPhase7UnifiedFeedback(unittest.TestCase):
    def setUp(self):
        init_db()
        self.schedule_mgr = UnifiedScheduleManager(commit_hash="phase7_test_commit")
        self.learning_mgr = UnifiedLearningManager(current_champion="v2.4-pooled-calibrated")
        self.ablation_engine = AblationStudyEngine()

    def test_immutable_decisions_hash_chain_and_tamper_detection(self):
        """Tests that decisions table enforces cryptographic SHA-256 hash chaining and detects tampering."""
        # Clean test table entries if needed or insert two sequential decisions
        h1 = insert_immutable_decision(
            timestamp="2026-11-17T14:00:00",
            data_vintage="2026-11-17",
            model_version="v2.4",
            threshold_version="th-1",
            feature_vector={"price": 814.0, "score": 82},
            forecast_distributions={"20d": {"mean": 3.8}},
            regime_probabilities={"BASE_RECOVERY": 0.65},
            tactical_levels={"order": "LIMIT_ORDER_PULLBACK"},
            tranche_pct=0.20,
            exact_shares=245,
            exact_cash_amount=199430.0,
            abstain_flag=0,
            decision_action="ACCUMULATE",
            code_commit_hash="commit_hash_1"
        )
        self.assertEqual(len(h1), 64)

        h2 = insert_immutable_decision(
            timestamp="2026-11-18T14:00:00",
            data_vintage="2026-11-18",
            model_version="v2.4",
            threshold_version="th-1",
            feature_vector={"price": 818.0, "score": 84},
            forecast_distributions={"20d": {"mean": 4.1}},
            regime_probabilities={"BASE_RECOVERY": 0.68},
            tactical_levels={"order": "MARKET_TRANCHE"},
            tranche_pct=0.25,
            exact_shares=305,
            exact_cash_amount=249490.0,
            abstain_flag=0,
            decision_action="ACCUMULATE",
            code_commit_hash="commit_hash_2"
        )
        self.assertEqual(len(h2), 64)

        # 1. Verify chain integrity passes
        is_valid, errors = verify_decision_chain_integrity()
        self.assertTrue(is_valid, f"Chain integrity failed: {errors}")

        # 2. Test Tamper Detection
        # Manually alter a row in SQLite
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM decisions ORDER BY id DESC LIMIT 1")
        last_id = cursor.fetchone()[0]
        # Maliciously change exact_shares without updating hash
        cursor.execute("UPDATE decisions SET exact_shares = 999999 WHERE id = ?", (last_id,))
        conn.commit()
        conn.close()

        # Chain verification MUST fail now
        tamper_valid, tamper_errors = verify_decision_chain_integrity()
        self.assertFalse(tamper_valid)
        self.assertTrue(any("tampered or mismatch" in err for err in tamper_errors))

        # Restore valid state for clean test environment
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM decisions WHERE id = ?", (last_id,))
        conn.commit()
        conn.close()

    def test_schedule_manager_execution_points(self):
        """Tests the 4 scheduled checkpoints: 08:45, 09:20, 14:00, 16:00 IST."""
        # 08:45 Data Integrity Check
        res_0845 = self.schedule_mgr.run_0845_data_integrity()
        self.assertEqual(res_0845["step"], "08:45_DATA_INTEGRITY_CHECK")
        self.assertIn("adr_inr_equivalent", res_0845)

        # 09:20 Regime Update (using external metrics only)
        res_0920 = self.schedule_mgr.run_0920_regime_update(india_vix=15.2, dist_sma_50=-0.03, fii_dii_net_flow_cr=250.0)
        self.assertEqual(res_0920["step"], "09:20_REGIME_UPDATE")
        self.assertIn(res_0920["regime"], ["BASE_RECOVERY", "CORRECTION"])

        # 14:00 Immutable Snapshot
        res_1400 = self.schedule_mgr.run_1400_immutable_snapshot(bottom_score=82, fundamental_score=84)
        self.assertEqual(res_1400["step"], "14:00_IMMUTABLE_SNAPSHOT")
        self.assertIn("row_hash", res_1400)
        self.assertGreater(res_1400["exact_shares"], 0)

        # 16:00 Mature Reconciliation
        res_1600 = self.schedule_mgr.run_1600_mature_reconciliation()
        self.assertEqual(res_1600["step"], "16:00_POST_MARKET_RECONCILIATION")
        self.assertIn("reconciled_horizons", res_1600)

    def test_learning_manager_drawdown_limit_invariant(self):
        """Tests non-negotiable rule: learning can NEVER widen max drawdown limit beyond 15%."""
        res_l3 = self.learning_mgr.layer3_tune_strategy(current_threshold=70.0, suggested_adjustment=2.0)
        self.assertFalse(res_l3["drawdown_limit_widened"])
        self.assertEqual(res_l3["max_drawdown_limit_pct"], 15.0)

    def test_champion_challenger_promotion_rules(self):
        """Tests that superior challenger requires manual approval and is NEVER auto-deployed."""
        # 1. Challenger beats champion across all 3 gates, but NO manual approval
        eval_no_approval = self.learning_mgr.layer4_evaluate_challenger(
            challenger_version="v2.5-challenger-candidate",
            champion_brier=0.210,
            challenger_brier=0.180,       # Lower is better (passed)
            champion_max_dd=0.140,
            challenger_max_dd=0.115,      # Lower is better (passed)
            champion_excess_return=4.2,
            challenger_excess_return=6.5,  # Higher is better (passed)
            manual_approval_granted=False  # No user sign-off
        )
        self.assertTrue(eval_no_approval.is_challenger_superior)
        self.assertEqual(eval_no_approval.deployment_status, "CHALLENGER_AWAITING_MANUAL_APPROVAL (Gates Passed, Promotion Locked)")

        # 2. Challenger with manual approval
        eval_approved = self.learning_mgr.layer4_evaluate_challenger(
            challenger_version="v2.5-challenger-candidate",
            champion_brier=0.210,
            challenger_brier=0.180,
            champion_max_dd=0.140,
            challenger_max_dd=0.115,
            champion_excess_return=4.2,
            challenger_excess_return=6.5,
            manual_approval_granted=True   # User approved
        )
        self.assertEqual(eval_approved.deployment_status, "DEPLOYED_ACTIVE (Manual Approval Confirmed)")

        # 3. Challenger fails drawdown gate
        eval_failed = self.learning_mgr.layer4_evaluate_challenger(
            challenger_version="v2.5-risky",
            champion_brier=0.210,
            challenger_brier=0.170,
            champion_max_dd=0.140,
            challenger_max_dd=0.190,       # Higher drawdown! Fails gate
            champion_excess_return=4.2,
            challenger_excess_return=8.0,
            manual_approval_granted=True
        )
        self.assertFalse(eval_failed.is_challenger_superior)
        self.assertEqual(eval_failed.deployment_status, "REJECTED (Failed Performance Gates)")

    def test_ablation_study_agent_contributions(self):
        """Tests that ablation study generates quantitative alpha breakdowns across Committee agents."""
        metrics = self.ablation_engine.generate_ablation_study()
        self.assertEqual(len(metrics), 5)
        # Verify monotonically improving Sharpe from baseline to full ensemble
        sharpes = [m.sharpe_ratio for m in metrics]
        self.assertEqual(sharpes, sorted(sharpes))
        # Incremental alpha must be positive for full ensemble
        self.assertGreater(metrics[-1].incremental_alpha_contribution_pct, 2.0)


if __name__ == "__main__":
    unittest.main()
