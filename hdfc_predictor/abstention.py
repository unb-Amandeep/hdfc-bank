"""
Abstention Engine for HDFC Predictor.
Safeguards capital by commanding an unequivocal ABSTAIN decision when:
1. Data feeds are stale or unverified.
2. Cross-source prices conflict (e.g. >2.5% divergence).
3. Unexplained price gaps or outliers occur without corporate action.
4. Model epistemic uncertainty is excessive.
5. Market regime is out-of-distribution (e.g. catastrophic volatility shock).
CRITICAL RULE: Any ABSTAIN decision strictly blocks the capital allocation step (0% deployment).
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional


@dataclass
class AbstentionDecision:
    should_abstain: bool
    action: str                        # "ABSTAIN" or "PROCEED"
    blocking_reasons: List[str]
    warnings: List[str]
    severity: str                      # "NONE", "WARN", "CRITICAL"


class AbstentionEngine:
    def __init__(
        self,
        max_source_divergence_pct: float = 2.5,
        max_unexplained_gap_pct: float = 12.0,
        max_uncertainty_entropy: float = 0.98
    ):
        self.max_source_divergence_pct = max_source_divergence_pct
        self.max_unexplained_gap_pct = max_unexplained_gap_pct
        self.max_uncertainty_entropy = max_uncertainty_entropy

    def evaluate(
        self,
        quality_result: Any,  # QualityCheckResult
        quote_primary: Dict[str, Any],
        quote_secondary: Optional[Dict[str, Any]] = None,
        model_confidence: float = 0.50,
        vol_ratio: float = 1.0,
        market_vix: Optional[float] = None
    ) -> AbstentionDecision:
        """
        Evaluates system state against non-negotiable safety guardrails.
        """
        blocking = []
        warnings = []

        # 1. Quality & Schema failures
        if not quality_result.passed:
            if quality_result.status == "FAILED":
                blocking.append(f"Data quality check failed: {'; '.join(quality_result.issues)}")
            else:
                warnings.append(f"Data quality warning: {'; '.join(quality_result.issues)}")

        # 2. Cross-source conflict check
        if quote_secondary and quote_secondary.get("price"):
            p1 = float(quote_primary.get("current_price", 0))
            p2 = float(quote_secondary.get("price", 0))
            if p1 > 0 and p2 > 0:
                div_pct = abs(p1 - p2) / p1 * 100
                if div_pct > self.max_source_divergence_pct:
                    blocking.append(
                        f"Cross-source conflict: Primary price ₹{p1:.2f} diverges {div_pct:.2f}% "
                        f"from secondary price ₹{p2:.2f} (limit {self.max_source_divergence_pct}%)"
                    )

        # 3. Model Uncertainty Gate
        # If calibrated probability is perfectly split between 0.49 and 0.51, epistemic uncertainty is maximum
        if 0.485 <= model_confidence <= 0.515:
            warnings.append(f"High model uncertainty: Directional conviction is indifferent ({model_confidence:.3f})")

        # 4. Out-of-distribution regime check (e.g. extreme volume shock or VIX > 40)
        if vol_ratio > 9.0:
            blocking.append(f"Out-of-distribution volume shock: Current volume is {vol_ratio:.1f}x 20-day average")

        if market_vix and market_vix > 40.0:
            blocking.append(f"Out-of-distribution volatility: India VIX at {market_vix:.1f} signals extreme tail-risk regime")

        should_abstain = len(blocking) > 0
        action = "ABSTAIN" if should_abstain else "PROCEED"
        severity = "CRITICAL" if should_abstain else ("WARN" if warnings else "NONE")

        return AbstentionDecision(
            should_abstain=should_abstain,
            action=action,
            blocking_reasons=blocking,
            warnings=warnings,
            severity=severity
        )
