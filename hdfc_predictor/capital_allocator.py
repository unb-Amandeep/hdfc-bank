"""
Smart Capital Allocation Engine for HDFC Bank Cyclical Accumulation.
Calculates staged tranche deployments, cash reserves, fair value ranges,
and downside scenario buffers across custom investment budgets.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from hdfc_predictor.config import settings
from hdfc_predictor.deterministic_risk import DeterministicRiskEngine, DeterministicTranchePlan


@dataclass
class CapitalPlan:
    total_investment_budget: float       # e.g. ₹10,00,000
    bottom_opportunity_score: int        # 0 - 100
    target_cumulative_allocation_pct: float # e.g. 20.0%
    proposed_deployment_cash: float      # e.g. ₹2,00,000
    reserve_capital_cash: float          # e.g. ₹8,00,000
    reserve_capital_pct: float           # e.g. 80.0%
    base_fair_value: float               # e.g. ₹920.00
    bull_case_target: float              # e.g. ₹1,050.00
    bear_case_floor: float               # e.g. ₹710.00
    margin_of_safety_pct: float          # e.g. +13.1% to Base Fair Value
    tranche_ladder_table: List[Dict[str, Any]]
    allocation_rationale: str
    deterministic_tranche: Optional[DeterministicTranchePlan] = None


class CapitalAllocator:
    def __init__(self, default_budget: float = 1000000.0):
        self.default_budget = default_budget

    def compute_allocation_plan(
        self,
        bottom_score: int,
        current_price: float,
        budget: float = None,
        abstention: Optional[Any] = None
    ) -> CapitalPlan:
        """
        Determines smart tranche deployment policy based on cyclical opportunity score.
        Blocks deployment to 0% if Abstention Engine flags a safety block.
        """
        total_budget = budget or self.default_budget

        # If Abstention Engine signals ABSTAIN, hard-block all deployment
        if abstention and getattr(abstention, "should_abstain", False):
            blocking_str = "; ".join(getattr(abstention, "blocking_reasons", ["System in ABSTAIN state"]))
            ladder = [
                {"score_range": "ALL TIERS BLOCKED", "target_pct": 0, "amount": 0, "status": "ABSTAIN: " + blocking_str}
            ]
            return CapitalPlan(
                total_investment_budget=total_budget,
                bottom_opportunity_score=bottom_score,
                target_cumulative_allocation_pct=0.0,
                proposed_deployment_cash=0.0,
                reserve_capital_cash=total_budget,
                reserve_capital_pct=100.0,
                base_fair_value=920.00,
                bull_case_target=1060.00,
                bear_case_floor=710.00,
                margin_of_safety_pct=round(((920.00 - current_price) / current_price) * 100, 1),
                tranche_ladder_table=ladder,
                allocation_rationale=f"CAPITAL DEPLOYMENT STRICTLY BLOCKED BY ABSTENTION ENGINE: {blocking_str}"
            )

        # Staged Allocation Ladder Rules
        ladder = [
            {"score_range": "Below 60", "target_pct": 0, "amount": 0, "status": "HOLD CASH (Wait for Margin of Safety)"},
            {"score_range": "60 – 69", "target_pct": 10, "amount": total_budget * 0.10, "status": "INITIAL TRANCHE (10% Starter)"},
            {"score_range": "70 – 79", "target_pct": 20, "amount": total_budget * 0.20, "status": "CONFIRMED ACCUMULATION (20% Allocation)"},
            {"score_range": "80 – 89", "target_pct": 30, "amount": total_budget * 0.30, "status": "HEAVY ACCUMULATION (30% Allocation)"},
            {"score_range": "90+", "target_pct": 40, "amount": total_budget * 0.40, "status": "MAX CONVICTION TRANCHE (40% Cap)"}
        ]

        if bottom_score >= 90:
            target_pct = 40.0
        elif bottom_score >= 80:
            target_pct = 30.0
        elif bottom_score >= 70:
            target_pct = 20.0
        elif bottom_score >= 60:
            target_pct = 10.0
        else:
            target_pct = 0.0

        deploy_cash = round(total_budget * (target_pct / 100.0), 2)
        reserve_cash = round(total_budget - deploy_cash, 2)
        reserve_pct = round(100.0 - target_pct, 1)

        # Fair Value Scenarios:
        # Base: 2.30x FY28 BVPS (~₹400) = ₹920
        # Bull: 2.65x FY28 BVPS = ₹1,060
        # Bear floor: 1.80x BVPS = ₹710
        base_fv = 920.00
        bull_tgt = 1060.00
        bear_floor = 710.00
        margin_of_safety = round(((base_fv - current_price) / current_price) * 100, 1)

        rationale = (
            f"With Bottom Opportunity Score at {bottom_score}/100, the system recommends deploying "
            f"{target_pct:.0f}% of your planned capital (₹{deploy_cash:,.0f}) in this accumulation band. "
            f"Crucially, {reserve_pct:.0f}% (₹{reserve_cash:,.0f}) is kept strictly in liquid reserve to buy deeper "
            f"tranches if the stock retests the Bear Case Floor of ₹{bear_floor:.0f}. "
            f"This prevents exhaustion of capital on initial pullbacks."
        )

        # Compute deterministic risk tranche
        risk_engine = DeterministicRiskEngine()
        deterministic_tranche = risk_engine.calculate_tranche(
            bottom_opportunity_score=bottom_score,
            current_price=current_price,
            portfolio_wealth=total_budget,
            abstention=abstention
        )

        return CapitalPlan(
            total_investment_budget=total_budget,
            bottom_opportunity_score=bottom_score,
            target_cumulative_allocation_pct=target_pct,
            proposed_deployment_cash=deploy_cash,
            reserve_capital_cash=reserve_cash,
            reserve_capital_pct=reserve_pct,
            base_fair_value=base_fv,
            bull_case_target=bull_tgt,
            bear_case_floor=bear_floor,
            margin_of_safety_pct=margin_of_safety,
            tranche_ladder_table=ladder,
            allocation_rationale=rationale,
            deterministic_tranche=deterministic_tranche
        )
