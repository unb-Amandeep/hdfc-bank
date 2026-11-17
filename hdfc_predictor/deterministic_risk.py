"""
Deterministic Risk & Capital Engine for HDFC Bank Cyclical Accumulation.

NON-NEGOTIABLE COMPLIANCE RULES:
1. Sizing is strictly deterministic and rule-based; zero LLM influence.
2. Max single-stock concentration cap: 15.0% of total wealth.
3. Drawdown dampener: scales down or halts new risk when portfolio drawdown approaches limits.
4. Volatility-scaled dynamic tranches replace static fixed splits.
5. Invalidation is fundamental/valuation-driven; trailing ratchets raise only on confirmed swing lows.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from hdfc_predictor.config import settings


@dataclass
class DeterministicTranchePlan:
    tranche_id: int
    tranche_label: str
    bottom_opportunity_score: int
    base_tranche_pct: float
    volatility_scale_factor: float
    drawdown_dampener_factor: float
    effective_tranche_pct: float
    exact_shares: int
    exact_cash_amount: float
    entry_limit_price: float
    execution_time_window_days: int
    fundamental_invalidation_price: float
    tactical_atr_reference: float
    trailing_ratchet_rule: str
    portfolio_wealth: float
    current_stock_weight_pct: float
    remaining_headroom_pct: float
    is_concentration_capped: bool
    is_drawdown_halted: bool
    time_in_cash_days: int
    time_in_cash_status: str
    rationale: str


class DeterministicRiskEngine:
    """
    Purely deterministic mathematical risk manager.
    No LLM, no hallucinated sizing. Every rupee is calculated from formulas.
    """

    MAX_CONCENTRATION_PCT = 0.15     # Max 15% single-stock wealth cap
    TARGET_VOLATILITY = 0.20         # 20% annualized target volatility
    MAX_PORTFOLIO_DD_LIMIT = 0.15    # 15% portfolio max drawdown tolerance
    TIME_IN_CASH_CAP_DAYS = 40       # Days in cash threshold

    def __init__(
        self,
        max_concentration: float = MAX_CONCENTRATION_PCT,
        target_volatility: float = TARGET_VOLATILITY,
        max_drawdown_limit: float = MAX_PORTFOLIO_DD_LIMIT
    ):
        self.max_concentration = max_concentration
        self.target_volatility = target_volatility
        self.max_drawdown_limit = max_drawdown_limit

    def calculate_tranche(
        self,
        bottom_opportunity_score: int,
        current_price: float,
        portfolio_wealth: float,
        current_position_value: float = 0.0,
        atr_14: float = 18.5,
        realized_vol_20d: float = 0.21,
        current_portfolio_drawdown: float = 0.0,
        days_in_cash: int = 15,
        book_value_per_share: float = 394.84,
        abstention: Optional[Any] = None,
        tranche_id: int = 1
    ) -> DeterministicTranchePlan:
        """
        Calculates exact shares, cash, entry limit, time window, and invalidation.
        """
        # 1. Abstention hard-block
        if abstention and getattr(abstention, "should_abstain", False):
            blocking_reasons = getattr(abstention, "blocking_reasons", ["System in ABSTAIN status"])
            return DeterministicTranchePlan(
                tranche_id=tranche_id,
                tranche_label="ABSTAIN_HALT",
                bottom_opportunity_score=bottom_opportunity_score,
                base_tranche_pct=0.0,
                volatility_scale_factor=1.0,
                drawdown_dampener_factor=0.0,
                effective_tranche_pct=0.0,
                exact_shares=0,
                exact_cash_amount=0.0,
                entry_limit_price=0.0,
                execution_time_window_days=0,
                fundamental_invalidation_price=round(book_value_per_share * 1.50, 1),
                tactical_atr_reference=atr_14,
                trailing_ratchet_rule="NO POSITION: Sizing locked by Abstention Engine.",
                portfolio_wealth=portfolio_wealth,
                current_stock_weight_pct=round((current_position_value / portfolio_wealth) * 100, 2),
                remaining_headroom_pct=round(max(0.0, self.max_concentration - (current_position_value / portfolio_wealth)) * 100, 2),
                is_concentration_capped=False,
                is_drawdown_halted=False,
                time_in_cash_days=days_in_cash,
                time_in_cash_status="ABSTAIN_ACTIVE",
                rationale=f"Zero allocation: Abstention active ({'; '.join(blocking_reasons)})."
            )

        # 2. Portfolio Concentration Limit Check (Max 15% single-stock)
        current_weight = current_position_value / max(1.0, portfolio_wealth)
        remaining_headroom = max(0.0, self.max_concentration - current_weight)
        max_allowed_stock_cash = portfolio_wealth * self.max_concentration
        max_allocatable_cash = portfolio_wealth * remaining_headroom
        is_concentration_capped = remaining_headroom <= 0.001

        # 3. Base Tranche Sizing Formula (Dynamic step-ladder)
        if bottom_opportunity_score < 60:
            base_pct = 0.0
            label = "HOLD_CASH"
        elif bottom_opportunity_score < 70:
            base_pct = 0.15  # 15% starter tranche
            label = "TRANCHE_1_STARTER"
        elif bottom_opportunity_score < 80:
            base_pct = 0.25  # 25% confirmed tranche
            label = "TRANCHE_2_CONFIRMED"
        elif bottom_opportunity_score < 90:
            base_pct = 0.40  # 40% deep-value tranche
            label = "TRANCHE_3_DEEP_VALUE"
        else:
            base_pct = 0.60  # 60% cyclical capitulation tranche
            label = "TRANCHE_MAX_CAPITULATION"

        # 4. Volatility Scaling
        # S_vol = Target_Vol / Realized_Vol clamped between 0.60 and 1.25
        safe_realized_vol = max(0.08, realized_vol_20d)
        vol_scale = round(min(1.25, max(0.60, self.target_volatility / safe_realized_vol)), 3)

        # 5. Portfolio Drawdown Dampener
        if current_portfolio_drawdown >= self.max_drawdown_limit:
            dd_dampener = 0.0
            is_dd_halted = True
        elif current_portfolio_drawdown > 0.05:  # Progressive reduction above 5% portfolio DD
            dd_dampener = round(max(0.0, 1.0 - (current_portfolio_drawdown / self.max_drawdown_limit)), 3)
            is_dd_halted = False
        else:
            dd_dampener = 1.0
            is_dd_halted = False

        # 6. Time-in-Cash Cap Check
        time_bonus = 0.0
        if bottom_opportunity_score >= 70 and days_in_cash >= self.TIME_IN_CASH_CAP_DAYS:
            time_bonus = 0.05  # +5% acceleration to prevent extreme cash drag at cyclical bottoms
            tic_status = f"ACCELERATED (Held cash {days_in_cash}d >= {self.TIME_IN_CASH_CAP_DAYS}d cap)"
        else:
            tic_status = f"NORMAL ({days_in_cash}d in cash)"

        # 7. Effective Tranche Percentage
        effective_pct = (base_pct + time_bonus) * vol_scale * dd_dampener
        effective_pct = round(min(1.0, max(0.0, effective_pct)), 4)

        # 8. Sizing Calculation (Rupees & Exact Shares)
        if is_concentration_capped or is_dd_halted or effective_pct <= 0.0:
            exact_cash = 0.0
            exact_shares = 0
        else:
            # Target cash is effective_pct of the maximum allowed allocation for the stock
            raw_target_cash = max_allowed_stock_cash * effective_pct
            # Clamped strictly by remaining headroom under 15% wealth cap
            clamped_cash = min(max_allocatable_cash, raw_target_cash)
            exact_shares = int(clamped_cash // current_price)
            exact_cash = round(exact_shares * current_price, 2)

        # 9. Tactical Order Parameters
        # Entry limit: 0.5 * ATR below current price for patient accumulation, or current price if score >= 90
        if bottom_opportunity_score >= 90:
            entry_limit = round(current_price, 1)
        else:
            entry_limit = round(max(current_price - (0.5 * atr_14), current_price * 0.95), 1)

        execution_window = 5  # 5 trading days validity

        # Fundamental Invalidation Price (1.50x Book Value = historic crisis low)
        fundamental_invalidation = round(book_value_per_share * 1.50, 1)

        # Ratchet Rule
        ratchet_rule = (
            "Raise stop ONLY on confirmed higher swing low on daily close; "
            "never trail on ATR alone to prevent shakeouts during accumulation."
        )

        # Rationale
        if is_concentration_capped:
            rat = f"Zero allocation: Position already at single-stock concentration cap ({current_weight*100:.1f}% >= {self.max_concentration*100:.0f}%)."
        elif is_dd_halted:
            rat = f"Zero allocation: Portfolio drawdown ({current_portfolio_drawdown*100:.1f}%) exceeds safety limit ({self.max_drawdown_limit*100:.0f}%)."
        elif exact_shares == 0:
            rat = f"Preserve 100% Cash: Opportunity score ({bottom_opportunity_score}/100) below accumulation threshold."
        else:
            rat = (
                f"Deploy Tranche {tranche_id} ({label}): Sized at {exact_shares} shares (₹{exact_cash:,.0f}). "
                f"Base={base_pct*100:.0f}%, Vol-Scale={vol_scale}x, DD-Dampener={dd_dampener}x. "
                f"Remaining single-stock headroom: {remaining_headroom*100:.1f}%."
            )

        return DeterministicTranchePlan(
            tranche_id=tranche_id,
            tranche_label=label,
            bottom_opportunity_score=bottom_opportunity_score,
            base_tranche_pct=base_pct,
            volatility_scale_factor=vol_scale,
            drawdown_dampener_factor=dd_dampener,
            effective_tranche_pct=effective_pct,
            exact_shares=exact_shares,
            exact_cash_amount=exact_cash,
            entry_limit_price=entry_limit,
            execution_time_window_days=execution_window,
            fundamental_invalidation_price=fundamental_invalidation,
            tactical_atr_reference=round(atr_14, 2),
            trailing_ratchet_rule=ratchet_rule,
            portfolio_wealth=portfolio_wealth,
            current_stock_weight_pct=round(current_weight * 100, 2),
            remaining_headroom_pct=round(remaining_headroom * 100, 2),
            is_concentration_capped=is_concentration_capped,
            is_drawdown_halted=is_dd_halted,
            time_in_cash_days=days_in_cash,
            time_in_cash_status=tic_status,
            rationale=rat
        )
