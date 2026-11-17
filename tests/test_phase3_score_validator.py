"""
Unit tests for Phase 3: Score Validation on Pooled Universe,
Decile Monotonicity, Purging & Embargo, and Weight Sensitivity.
"""
import unittest
import numpy as np
import pandas as pd

from hdfc_predictor.score_validator import ScoreValidator, DecileBucketResult


class TestPhase3ScoreValidator(unittest.TestCase):
    def test_01_effective_sample_size(self):
        """Verifies degrees of freedom accounting for overlapping forward return horizons."""
        n_eff_daily = ScoreValidator.compute_effective_sample_size(total_rows=500, horizon_days=1)
        self.assertEqual(n_eff_daily, 500)

        n_eff_60d = ScoreValidator.compute_effective_sample_size(total_rows=500, horizon_days=60)
        self.assertEqual(n_eff_60d, 8)  # 500 / 60 = 8.33 -> 8 independent non-overlapping chunks

        n_eff_252d = ScoreValidator.compute_effective_sample_size(total_rows=500, horizon_days=252)
        self.assertEqual(n_eff_252d, 1)

    def test_02_purging_and_embargo(self):
        """Verifies that purging removes forward overlap before test set and adds embargo buffer."""
        dates = pd.date_range("2024-01-01", periods=200, freq="B")
        df = pd.DataFrame({"val": range(200)}, index=dates)

        split_idx = 100
        horizon = 20
        embargo = 5

        train_df, test_df = ScoreValidator.apply_purging_and_embargo(df, split_idx, horizon_days=horizon, embargo_days=embargo)

        # Train set must stop at least 20 bars before split_idx (100 - 20 = 80)
        self.assertEqual(len(train_df), 80)
        # Test set must start at least 5 bars after split_idx (100 + 5 = 105 -> 95 remaining)
        self.assertEqual(len(test_df), 95)
        # No index overlap
        self.assertFalse(train_df.index.isin(test_df.index).any())

    def test_03_monotonicity_checker(self):
        """Tests that decile evaluator flags non-monotonic score relationships."""
        np.random.seed(42)
        n = 150
        # Perfectly correlated scores with forward returns (monotonic)
        scores_good = np.linspace(20, 95, n)
        ret_60d_good = scores_good * 0.25 + np.random.normal(0, 1.0, n)
        
        buckets, status, flags = ScoreValidator.evaluate_score_monotonicity(
            scores=scores_good,
            forward_returns={60: ret_60d_good},
            num_buckets=5
        )
        self.assertEqual(len(buckets), 5)
        self.assertTrue(status.get("is_monotonic_60d", False))
        self.assertEqual(len(flags), 0)

        # Inverted / Non-monotonic returns (Bucket 5 performs worse than Bucket 1)
        ret_60d_bad = -scores_good * 0.20 + np.random.normal(0, 1.0, n)
        buckets_bad, status_bad, flags_bad = ScoreValidator.evaluate_score_monotonicity(
            scores=scores_good,
            forward_returns={60: ret_60d_bad},
            num_buckets=5
        )
        self.assertFalse(status_bad.get("is_monotonic_60d", True))
        self.assertGreater(len(flags_bad), 0)
        self.assertIn("violated monotonicity", flags_bad[0])

    def test_04_weight_sensitivity(self):
        """Verifies that +/- 20% weight perturbation maintains score rank stability."""
        np.random.seed(99)
        n_samples = 200
        sample_matrix = pd.DataFrame({
            "val_attractiveness": np.random.uniform(30, 90, n_samples),
            "fund_strength": np.random.uniform(50, 95, n_samples),
            "tech_formation": np.random.uniform(20, 80, n_samples),
            "rel_valuation": np.random.uniform(40, 90, n_samples),
            "inst_confirmation": np.random.uniform(30, 75, n_samples)
        })

        base_weights = {
            "val_attractiveness": 0.30,
            "fund_strength": 0.25,
            "tech_formation": 0.20,
            "rel_valuation": 0.15,
            "inst_confirmation": 0.10
        }

        res = ScoreValidator.test_weight_sensitivity(base_weights, sample_matrix, perturbation_pct=0.20)
        self.assertTrue(res["is_score_robust"])
        self.assertGreaterEqual(res["min_rank_correlation"], 0.92)


if __name__ == "__main__":
    unittest.main()
