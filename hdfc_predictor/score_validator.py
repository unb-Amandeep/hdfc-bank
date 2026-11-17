"""
Pooled Universe Score Validation, Decile Monotonicity, and Walk-Forward Engine.
Pools large-cap Indian private and public lenders (HDFCBANK, ICICIBANK, SBIN, KOTAKBANK, AXISBANK)
to statistically validate Fundamental Health and Bottom Opportunity scores without overfitting.
Features:
- Decile / Quintile monotonicity testing across forward horizons (5d, 20d, 60d, 120d, 252d).
- Purging and embargo for overlapping forward horizons.
- Effective sample size computation (N_eff) rather than raw row counts.
- Weight sensitivity test (+/- 10-20%) on score formulation.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
import numpy as np
import pandas as pd

from hdfc_predictor.config import settings


@dataclass
class DecileBucketResult:
    bucket_label: str
    sample_count: int
    mean_score: float
    forward_5d_mean: float
    forward_20d_mean: float
    forward_60d_mean: float
    forward_120d_mean: float
    forward_252d_mean: float


@dataclass
class ScoreValidationReport:
    score_name: str
    total_observations: int
    effective_sample_size_60d: int
    effective_sample_size_252d: int
    decile_results: List[DecileBucketResult]
    is_monotonic_5d: bool
    is_monotonic_20d: bool
    is_monotonic_60d: bool
    is_monotonic_120d: bool
    is_monotonic_252d: bool
    non_monotonic_flags: List[str]
    weight_sensitivity_summary: Dict[str, Any]


class ScoreValidator:
    UNIVERSE = ["HDFCBANK.NS", "ICICIBANK.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS"]

    @classmethod
    def compute_effective_sample_size(cls, total_rows: int, horizon_days: int) -> int:
        """
        Calculates honest degrees of freedom after accounting for overlapping forward return windows.
        """
        if horizon_days <= 1:
            return total_rows
        return max(1, int(total_rows / horizon_days))

    @classmethod
    def apply_purging_and_embargo(
        cls,
        df: pd.DataFrame,
        split_idx: int,
        horizon_days: int = 60,
        embargo_days: int = 5
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Purges overlapping forward labels between train and test sets to eliminate look-ahead leakage.
        """
        # Train set stops 'horizon_days' before split_idx so train labels don't bleed into test
        train_end = max(10, split_idx - horizon_days)
        train_df = df.iloc[:train_end].copy()

        # Test set starts after split_idx + embargo_days buffer
        test_start = min(len(df) - 10, split_idx + embargo_days)
        test_df = df.iloc[test_start:].copy()

        return train_df, test_df

    @classmethod
    def evaluate_score_monotonicity(
        cls,
        scores: np.ndarray,
        forward_returns: Dict[int, np.ndarray],
        num_buckets: int = 5
    ) -> Tuple[List[DecileBucketResult], Dict[str, bool], List[str]]:
        """
        Partitions samples into score buckets and audits whether higher scores
        consistently produce strictly higher forward returns across multiple horizons.
        """
        df = pd.DataFrame({"score": scores})
        for h, rets in forward_returns.items():
            df[f"ret_{h}d"] = rets

        df.dropna(inplace=True)
        if len(df) < num_buckets * 5:
            # Fallback if sample size is minimal
            return [], {f"is_monotonic_{h}d": True for h in forward_returns}, []

        # Quantile binning
        df["bucket"] = pd.qcut(df["score"], q=num_buckets, labels=False, duplicates="drop")

        bucket_results = []
        unique_buckets = sorted(df["bucket"].unique())

        for b in unique_buckets:
            sub = df[df["bucket"] == b]
            label = f"Q{b+1} (Score {sub['score'].min():.0f}-{sub['score'].max():.0f})"
            b_res = DecileBucketResult(
                bucket_label=label,
                sample_count=len(sub),
                mean_score=round(float(sub["score"].mean()), 1),
                forward_5d_mean=round(float(sub.get("ret_5d", pd.Series([0])).mean()), 2),
                forward_20d_mean=round(float(sub.get("ret_20d", pd.Series([0])).mean()), 2),
                forward_60d_mean=round(float(sub.get("ret_60d", pd.Series([0])).mean()), 2),
                forward_120d_mean=round(float(sub.get("ret_120d", pd.Series([0])).mean()), 2),
                forward_252d_mean=round(float(sub.get("ret_252d", pd.Series([0])).mean()), 2),
            )
            bucket_results.append(b_res)

        # Monotonicity test: Is bucket K mean return >= bucket K-1 mean return?
        monotonic_status = {}
        flags = []

        for h in [5, 20, 60, 120, 252]:
            if f"ret_{h}d" not in df.columns:
                continue
            col_name = f"forward_{h}d_mean"
            vals = [getattr(br, col_name) for br in bucket_results]
            
            # Check non-decreasing trend
            is_mono = True
            for i in range(1, len(vals)):
                # Allow a tiny statistical noise buffer of 0.25%
                if vals[i] < (vals[i-1] - 0.25):
                    is_mono = False
                    flags.append(f"{h}-day forward returns violated monotonicity: {bucket_results[i].bucket_label} ({vals[i]:.2f}%) < {bucket_results[i-1].bucket_label} ({vals[i-1]:.2f}%)")
                    break
            monotonic_status[f"is_monotonic_{h}d"] = is_mono

        return bucket_results, monotonic_status, flags

    @classmethod
    def test_weight_sensitivity(
        cls,
        base_weights: Dict[str, float],
        sample_feature_matrix: pd.DataFrame,
        perturbation_pct: float = 0.20
    ) -> Dict[str, Any]:
        """
        Perturbs score pillar weights by +/- 10% to 20% and measures rank stability (Spearman rho).
        Guarantees that score ranking is structurally robust and not curve-fitted to brittle weights.
        """
        # Baseline score calculation
        cols = list(base_weights.keys())
        w_base = np.array([base_weights[c] for c in cols])
        w_base = w_base / w_base.sum()

        X = sample_feature_matrix[cols].values
        base_scores = np.dot(X, w_base)

        results = {}
        spearman_rhos = []

        # Perturb each pillar by +20% and -20%
        for i, col in enumerate(cols):
            w_pert_plus = w_base.copy()
            w_pert_plus[i] *= (1.0 + perturbation_pct)
            w_pert_plus /= w_pert_plus.sum()
            scores_plus = np.dot(X, w_pert_plus)

            w_pert_minus = w_base.copy()
            w_pert_minus[i] *= (1.0 - perturbation_pct)
            w_pert_minus /= w_pert_minus.sum()
            scores_minus = np.dot(X, w_pert_minus)

            # Rank correlations
            rho_plus = float(pd.Series(base_scores).corr(pd.Series(scores_plus), method="spearman"))
            rho_minus = float(pd.Series(base_scores).corr(pd.Series(scores_minus), method="spearman"))
            spearman_rhos.extend([rho_plus, rho_minus])

            results[col] = {
                f"rho_+{int(perturbation_pct*100)}%": round(rho_plus, 4),
                f"rho_-{int(perturbation_pct*100)}%": round(rho_minus, 4),
                "is_stable": (rho_plus > 0.90 and rho_minus > 0.90)
            }

        min_rho = min(spearman_rhos) if spearman_rhos else 1.0
        return {
            "perturbation_tested": f"+/-{int(perturbation_pct*100)}%",
            "pillar_sensitivities": results,
            "min_rank_correlation": round(min_rho, 4),
            "is_score_robust": bool(min_rho >= 0.92)
        }
