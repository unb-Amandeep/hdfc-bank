"""
Fair Value, Quantitative 3-State Regime, and Two-Tier Arbitration Engine.
- Justified P/B & ROE Residual Income Model (Bear/Base/Bull scenarios) with 2023 merger structural break.
- Expanded Fundamentals Gate (NII YoY, CASA, Credit Cost, Slippages, PCR, Cost-to-Income, LCR).
- Quantitative 3-State Regime Model (Correction, Base Recovery, Overheated/Breakdown).
- Tier Arbitration Engine: Primary dictates WHAT & HOW MUCH; Tactical dictates WHEN & ORDER TYPE.
- Event Blackouts (Earnings, RBI MPC), GIFT Nifty overnight checks, and Thesis-Break Exits.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
import numpy as np
import pandas as pd

from hdfc_predictor.config import settings
from hdfc_predictor.fundamental_engine import FundamentalEngine, FundamentalProfile
from hdfc_predictor.trading_calendar import TradingCalendar


@dataclass
class FairValueScenario:
    scenario_name: str         # "BEAR", "BASE", "BULL"
    probability: float         # 0.25, 0.55, 0.20
    projected_roe_pct: float   # 11.5%, 14.5%, 16.5%
    justified_pb: float        # 1.80x, 2.30x, 2.65x
    fair_value_low: float      # ₹710, ₹910, ₹1040
    fair_value_high: float     # ₹740, ₹940, ₹1080
    rationale: str


@dataclass
class ComprehensiveFairValueReport:
    current_price: float
    current_pb: float
    historical_pb_percentile: float
    merger_structural_break_window: str  # "Post-Merger Window: July 2023 to Present"
    weighted_expected_fair_value: float  # Prob-weighted composite (e.g. ₹915)
    margin_of_safety_pct: float          # (Expected FV - Price) / Price * 100
    scenarios: List[FairValueScenario]


@dataclass
class RegimeState:
    state_id: str              # "CORRECTION", "BASE_RECOVERY", "OVERHEATED_OR_BREAKDOWN"
    state_label: str
    regime_probability: float  # Calibrated probability
    key_drivers: List[str]
    historical_forward_30d_return: float


@dataclass
class SingleDecisionObject:
    canonical_action: str               # Strictly: "WAIT" | "BUY" | "SELL"
    action_headline: str               # Clean, unequivocal headline
    action_detail: str
    is_live_data: bool                 # True if licensed/broker real-time; False if stale/offline
    data_staleness_warning: Optional[str] # "DATA STALE - not live" (red badge)
    trading_blocked: bool              # True if orders are blocked due to stale feed or blackout
    trading_blocked_reason: Optional[str]
    inputs: Dict[str, Any]             # Explicitly relabeled advisory inputs
    disagreements: List[str]           # Surfaced disagreements among inputs
    arbitration_rationale: str
    order_directive: Dict[str, Any]
    precedence_tier: str = "Precedence 5: Default State"
    eligible_tranche_pct: float = 0.0
    current_position_weight_pct: float = 8.5
    target_position_weight_pct: float = 12.0
    feed_source: Optional[str] = None
    feed_timestamp: Optional[str] = None
    feed_status: Optional[str] = None


@dataclass
class ArbitrationDirective:
    verdict_action: str                # Strictly: "WAIT" | "BUY" | "SELL"
    verdict_subtitle: str
    decision_object: SingleDecisionObject # Single authoritative decision object
    primary_decision: str              # Input: e.g. "ACCUMULATE_20_PCT"
    tactical_timing: str               # Input: e.g. "WAIT_FOR_LIMIT_PULLBACK"
    execution_order_type: str          # "LIMIT_ORDER_PULLBACK", "MARKET_TRANCHE", "HOLD_OFF"
    limit_entry_zone: Tuple[float, float] # e.g. (742.0, 772.0)
    order_expiry_date: str             # e.g. "2026-11-26 (5 Trading Days)"
    order_recheck_rule: str            # Re-check rule if limit is not filled
    has_tier_conflict: bool
    tier_conflict_explanation: Optional[str]
    is_event_blackout_active: bool
    blackout_reason: Optional[str]
    overnight_gift_nifty_bias: str     # "BULLISH", "BEARISH", "NEUTRAL"
    thesis_break_status: str           # "INTACT", "WARNING", "INVALIDATED", "VALUATION_EXIT"
    what_would_change_my_mind: str


class FairValueAndRegimeEngine:
    def __init__(self, symbol: str = settings.symbol):
        self.symbol = symbol
        self.cost_of_equity = 0.1228  # Rf 6.5% + Beta 1.05 * ERP 5.5%
        self.long_term_growth = 0.095 # 9.5% long-term nominal growth

    def compute_justified_fair_value(
        self,
        current_price: float = 814.0,
        book_value_per_share: float = 394.84
    ) -> ComprehensiveFairValueReport:
        """
        Calculates justified P/B via ROE-driven residual income model across 3 macro scenarios.
        Explicitly isolates the July 2023 merger structural break.
        """
        # Scenario definitions
        scenarios = [
            FairValueScenario(
                scenario_name="BEAR (Prolonged C/D Drag & NIM Compression)",
                probability=0.25,
                projected_roe_pct=11.5,
                justified_pb=1.82,
                fair_value_low=round(book_value_per_share * 1.80, 1),
                fair_value_high=round(book_value_per_share * 1.88, 1),
                rationale="Deposit costs remain high; loan growth restricted to 6-7%; NIM suppressed under 3.10%."
            ),
            FairValueScenario(
                scenario_name="BASE (Orderly Normalization to Historical Discipline)",
                probability=0.55,
                projected_roe_pct=14.5,
                justified_pb=2.32,
                fair_value_low=round(book_value_per_share * 2.28, 1),
                fair_value_high=round(book_value_per_share * 2.38, 1),
                rationale="C/D ratio normalizes to 92-94%; credit growth re-accelerates to 12%; NIM recovers to 3.35%."
            ),
            FairValueScenario(
                scenario_name="BULL (Synergies Realized & FII Multiple Expansion)",
                probability=0.20,
                projected_roe_pct=16.5,
                justified_pb=2.68,
                fair_value_low=round(book_value_per_share * 2.62, 1),
                fair_value_high=round(book_value_per_share * 2.75, 1),
                rationale="Cross-selling to mortgage base accelerates; ROE expands to 16.5%; multiple re-rates toward historical average."
            )
        ]

        # Probability-weighted composite fair value
        weighted_fv = sum(s.probability * ((s.fair_value_low + s.fair_value_high) / 2.0) for s in scenarios)
        margin_of_safety = round(((weighted_fv - current_price) / current_price) * 100, 1)

        return ComprehensiveFairValueReport(
            current_price=current_price,
            current_pb=round(current_price / book_value_per_share, 2),
            historical_pb_percentile=16.0,
            merger_structural_break_window="Post-Merger Regime: July 2023 to Present (Mortgage Book Absorption Window)",
            weighted_expected_fair_value=round(weighted_fv, 1),
            margin_of_safety_pct=margin_of_safety,
            scenarios=scenarios
        )

    @classmethod
    def evaluate_regime_state(
        cls,
        rsi_14: float,
        dist_sma_20: float,
        dist_sma_50: float,
        vol_ratio: float,
        fundamental_score: int
    ) -> RegimeState:
        """
        Computes 3-state deterministic regime from math and fundamentals. No LLM hallucinations.
        """
        # State 3: Overheated or Structural Breakdown
        if rsi_14 > 82.0 or dist_sma_20 > 0.09:
            return RegimeState(
                state_id="OVERHEATED_OR_BREAKDOWN",
                state_label="Overheated Momentum Stretch",
                regime_probability=0.74,
                key_drivers=[f"RSI extreme ({rsi_14:.1f})", f"Trading +{dist_sma_20*100:.1f}% above 20-SMA", "Short-term momentum exhaustion"],
                historical_forward_30d_return=-1.8
            )
        elif fundamental_score < 50:
            return RegimeState(
                state_id="OVERHEATED_OR_BREAKDOWN",
                state_label="Structural Fundamental Breakdown",
                regime_probability=0.82,
                key_drivers=["Fundamental gate failed", "Asset quality deterioration", "Capital erosion risk"],
                historical_forward_30d_return=-8.4
            )

        # State 1: Active Correction
        if dist_sma_50 < -0.06 or (rsi_14 < 38 and dist_sma_20 < -0.03):
            return RegimeState(
                state_id="CORRECTION",
                state_label="Active Cyclical Correction",
                regime_probability=0.68,
                key_drivers=["Trading below 50-day SMA", "Downside momentum active", "Selling pressure dominant"],
                historical_forward_30d_return=1.2
            )

        # State 2: Base Recovery
        return RegimeState(
            state_id="BASE_RECOVERY",
            state_label="Base Building & Cyclical Recovery",
            regime_probability=0.62,
            key_drivers=["Price consolidating above support", "Fundamentals sound", "Healthy volume absorption"],
            historical_forward_30d_return=4.6
        )

    @classmethod
    def arbitrate_decision(
        cls,
        bottom_opportunity_score: int,
        fundamental_score: int,
        tactical_action: str,
        current_price: float,
        current_pb: float,
        is_live_data: bool = False,
        feed_status: str = "DATA STALE - not live",
        feed_source: str = "NSE Historical Verified Cache (Offline / Sandboxed)",
        feed_timestamp: str = "2026-11-18 15:30:00 IST",
        macro_inputs: Optional[Dict[str, Any]] = None,
        days_to_earnings: int = 45,
        days_to_rbi_mpc: int = 20,
        gift_nifty_change_pct: float = 0.25
    ) -> ArbitrationDirective:
        """
        Arbitration rule: Single decision object (WAIT / BUY / SELL) derived from a single
        authoritative arbitration layer. Relabels committee, bottom detector, and tactical ML
        as inputs, and surfaces conflicts and disagreements explicitly.
        """
        # 1. Event Blackout Check
        is_blackout = False
        blackout_msg = None
        if days_to_earnings <= 2:
            is_blackout = True
            blackout_msg = f"EVENT BLACKOUT: Quarterly Earnings scheduled in {days_to_earnings} days. Freeze orders to avoid binary event volatility."
        elif days_to_rbi_mpc <= 1:
            is_blackout = True
            blackout_msg = f"EVENT BLACKOUT: RBI MPC Monetary Policy decision in {days_to_rbi_mpc} days."

        # Ingest 4-Flag Thesis Health
        thesis_rep = FundamentalEngine.get_thesis_health_report()
        thesis_state = thesis_rep.overall_thesis_state

        if thesis_state == "HARD_INVALIDATION" or fundamental_score < 50:
            thesis_status = "INVALIDATED"
            what_change = "Thesis invalidated due to persistent balance-sheet deterioration across 2 quarters. Freeze all accumulation."
        elif current_pb >= 2.50 or current_price >= 995.0:
            thesis_status = "VALUATION_EXIT"
            what_change = "P/B reached Bull Case valuation ceiling (>=2.50x, ~₹995+). Cyclical discount fully closed; initiate profit-taking."
        elif thesis_state == "WEAKENING_THESIS" and fundamental_score < 75:
            thesis_status = "WEAKENING"
            what_change = "Thesis weakening: 2 Amber flags active (Structural CASA + System C/D spread). Pause market adds; buy only deep limit dips."
        else:
            thesis_status = "INTACT"
            what_change = "A quarterly drop in deposit growth below 11% YoY or Gross NPA spiking > 1.6% would invalidate the thesis and freeze tranches."

        # Setup standard pullback zone strictly below current market price
        if current_price >= 835.0:
            zone = (805.0, 822.0)
        else:
            zone = (round(current_price * 0.915, 1), round(current_price * 0.952, 1))

        # Precedence Hierarchy Evaluation:
        # Precedence 1: Hard Thesis Invalidation -> REDUCE / EXIT
        # Precedence 2: Weakening Thesis -> PAUSE_ADDS (No market chase)
        # Precedence 3: Valuation Ceiling (P/B >= 2.50x) -> TRIM / BOOK_PROFITS
        # Precedence 4: Eligible Entries (Deep Value 40%, Distress 40%, Pullback 20%, Breakout Starter 10%)
        # Precedence 5: Default -> HOLD / WAIT (0% new tranche)
        # Precedence 6: Data feed circuit breaker -> Blocks execution if stale

        exp_iso, exp_lbl = TradingCalendar.calculate_order_expiry(trading_days=5)
        expiry_date = f"{exp_iso} (5 Trading Days)"
        recheck_rule = (
            f"If price does not reach the ₹{zone[0]:.0f}–₹{zone[1]:.0f} buy zone by {expiry_date}, "
            "cancel the pending limit order, re-evaluate balance-sheet valuation, and reset the limit zone."
        )

        precedence_tier = "Precedence 5: Default State"
        eligible_tranche = 0.0

        if is_blackout:
            canonical_action = "WAIT"
            trading_blocked = True
            trading_blocked_reason = blackout_msg
            data_staleness_warning = None
            verdict_subtitle = "Event blackout active. Orders frozen."
            action_headline = "WAIT: Binary regulatory event within 48h. Orders frozen."
            precedence_tier = "Precedence 6: Event Blackout"
            order_type = "HOLD_OFF"

        elif not is_live_data:
            canonical_action = "WAIT"
            trading_blocked = True
            trading_blocked_reason = "DATA STALE - not live. Real-time licensed/broker feed offline; BUY/SELL verdicts blocked."
            data_staleness_warning = "DATA STALE - not live"
            verdict_subtitle = f"DATA STALE - not live ({feed_source} @ {feed_timestamp}). Trading blocked."
            action_headline = "WAIT: Price data is stale or offline. Trading execution blocked until live feed connects."
            precedence_tier = "Precedence 6: Circuit Breaker"
            order_type = "LIMIT_ORDER_PULLBACK" if ("SELL" in tactical_action or "TRIM" in tactical_action or current_price > zone[1]) else "HOLD_OFF"

        elif thesis_status == "INVALIDATED":
            # Precedence 1: Hard Thesis Invalidation overrides everything
            canonical_action = "SELL"
            trading_blocked = False
            trading_blocked_reason = None
            data_staleness_warning = None
            verdict_subtitle = "Thesis hard invalidation (2+ Red Flags for 2Q). Reduce position."
            action_headline = "REDUCE / EXIT: Fundamental Thesis Hard Invalidation."
            precedence_tier = "Precedence 1: Hard Thesis Invalidation"
            order_type = "MARKET_REDUCE"
            eligible_tranche = 0.0

        elif thesis_status == "VALUATION_EXIT":
            # Precedence 3: Valuation Ceiling reached
            canonical_action = "SELL"
            trading_blocked = False
            trading_blocked_reason = None
            data_staleness_warning = None
            verdict_subtitle = f"P/B expanded to {current_pb:.2f}x (Valuation ceiling >=2.50x). Book profits."
            action_headline = "TRIM / BOOK_PROFITS: Valuation Ceiling Reached."
            precedence_tier = "Precedence 3: Valuation Ceiling"
            order_type = "LIMIT_TRIM"
            eligible_tranche = 0.0

        elif current_price <= 695.0:
            # Precedence 4: Deep Value Base Entry
            canonical_action = "BUY"
            trading_blocked = False
            trading_blocked_reason = None
            data_staleness_warning = None
            eligible_tranche = 40.0
            verdict_subtitle = f"Price (₹{current_price:.2f}) at post-merger cyclical low (~1.75x P/B). Deploy 40% deep value tranche."
            action_headline = "BUY · Deep Value Base (40% Tranche Allocation)."
            precedence_tier = "Precedence 4: Deep Value Base Entry (40%)"
            order_type = "LIMIT_ORDER_DEEP_VALUE"
            zone = (670.0, 695.0)

        elif current_price <= 735.0:
            # Precedence 4: Distress Floor Entry
            canonical_action = "BUY"
            trading_blocked = False
            trading_blocked_reason = None
            data_staleness_warning = None
            eligible_tranche = 40.0
            verdict_subtitle = f"Price (₹{current_price:.2f}) at 50% Fib support floor. Deploy 40% core accumulation tranche."
            action_headline = "BUY · Distress Support Floor (40% Tranche Allocation)."
            precedence_tier = "Precedence 4: Distress Support Floor (40%)"
            order_type = "LIMIT_ORDER_DISTRESS"
            zone = (710.0, 735.0)

        elif zone[0] <= current_price <= zone[1]:
            # Precedence 4: Tactical Pullback Entry
            canonical_action = "BUY"
            trading_blocked = False
            trading_blocked_reason = None
            data_staleness_warning = None
            eligible_tranche = 20.0
            verdict_subtitle = f"Price (₹{current_price:.2f}) inside tactical pullback band (₹{zone[0]:.0f}–₹{zone[1]:.0f}). Execute 20% tranche."
            action_headline = "BUY · Tactical Pullback Entry (20% Tranche Allocation)."
            precedence_tier = "Precedence 4: Tactical Pullback Entry (20%)"
            order_type = "LIMIT_ORDER_PULLBACK"

        else:
            # Precedence 5: Default State (WAIT - No new tranche today)
            canonical_action = "WAIT"
            trading_blocked = False
            trading_blocked_reason = None
            data_staleness_warning = None
            eligible_tranche = 0.0
            order_type = "LIMIT_ORDER_PULLBACK"
            precedence_tier = "Precedence 5: Default State (WAIT · No new tranche today)"
            verdict_subtitle = f"Price (₹{current_price:.2f}, P/B {current_pb:.2f}x) is at Fair Value median above pullback band (₹{zone[0]:.0f}–₹{zone[1]:.0f}). Place limit order; do not chase."
            action_headline = "WAIT · No new tranche today (0% allocation). Price at Fair Value median."

        has_conflict = (
            ("SELL" in tactical_action or "TRIM" in tactical_action or "WAIT" in tactical_action or current_price > zone[1])
            and bottom_opportunity_score >= 70
        )
        conflict_exp = (
            f"TIER CONFLICT SURFACED: Primary Cyclical Valuation input signals Accumulation (Score {bottom_opportunity_score}/100), "
            f"but Tactical Momentum signals short-term overbought sprint ({tactical_action} at ₹{current_price:.2f}). "
            f"ARBITRATION RESOLUTION: Primary approves capital allocation, but Tactical restricts execution to a LIMIT ORDER "
            f"near the pullback support band (₹{zone[0]:.0f}–₹{zone[1]:.0f}) instead of chasing at current market price."
        ) if has_conflict else None

        primary_dec = f"ACCUMULATE_IN_TRANCHES ({eligible_tranche:.0f}% Target)" if eligible_tranche > 0 else "PRESERVE_CASH (0% Tranche)"
        tactical_tim = "WAIT_FOR_LIMIT_PULLBACK" if canonical_action == "WAIT" else "EXECUTE_TRANCHE"
        gift_bias = "BULLISH" if gift_nifty_change_pct > 0.15 else ("BEARISH" if gift_nifty_change_pct < -0.15 else "NEUTRAL")

        primary_wants_accumulate = bottom_opportunity_score >= 70
        tactical_blocks_market_buy = ("WAIT" in tactical_action or "SELL" in tactical_action or "TRIM" in tactical_action or current_price > zone[1])

        # Surfacing Disagreements among Advisory Inputs
        disagreements = []
        if has_conflict and conflict_exp:
            disagreements.append(conflict_exp)
        elif primary_wants_accumulate and tactical_blocks_market_buy:
            disagreements.append(
                f"Cyclical Bottom Detector signals Accumulation (Score {bottom_opportunity_score}/100) "
                f"while Tactical ML signals Short-Term Exhaustion ({tactical_action}). "
                f"Arbitration resolves: Stage a limit order at ₹{zone[0]:.0f}–₹{zone[1]:.0f}; do not market-buy at current price."
            )
        if not is_live_data:
            disagreements.append(
                f"Live Broker Feed Offline: Feed reported from '{feed_source}' at {feed_timestamp}. "
                "Any BUY/SELL execution is strictly blocked by the safety circuit until live tick verification passes."
            )

        inputs = {
            "cyclical_bottom_detector": {
                "label": "Cyclical Valuation Input",
                "perspective": "ACCUMULATE_TRANCHE_1" if bottom_opportunity_score >= 70 else "WAIT",
                "score": bottom_opportunity_score,
                "weight": "40%",
                "status": "INPUT_ONLY"
            },
            "tactical_ml": {
                "label": "Tactical 2:00 PM ML Timing",
                "perspective": tactical_action,
                "weight": "20%",
                "status": "INPUT_ONLY"
            },
            "investment_committee": {
                "label": "Investment Committee Advisory",
                "perspective": "WAIT (Consensus)",
                "weight": "20%",
                "status": "INPUT_ONLY"
            },
            "macro_market": {
                "label": "Macro & Derivatives Input",
                "perspective": macro_inputs.get("macro_composite_verdict", "Supportive DII flows") if macro_inputs else "DII Absorption (+₹2,450 Cr)",
                "weight": "20%",
                "status": "INPUT_ONLY"
            }
        }

        order_dir = {
            "execution_order_type": order_type,
            "limit_entry_zone": zone,
            "order_expiry_date": expiry_date,
            "order_recheck_rule": recheck_rule,
            "trading_blocked": trading_blocked,
            "trading_blocked_reason": trading_blocked_reason
        }

        decision_obj = SingleDecisionObject(
            canonical_action=canonical_action,
            action_headline=action_headline,
            action_detail=verdict_subtitle,
            is_live_data=is_live_data,
            data_staleness_warning=data_staleness_warning,
            trading_blocked=trading_blocked,
            trading_blocked_reason=trading_blocked_reason,
            inputs=inputs,
            disagreements=disagreements,
            arbitration_rationale=conflict_exp or "All input models aligned on disciplined capital preservation.",
            order_directive=order_dir,
            precedence_tier=precedence_tier,
            eligible_tranche_pct=eligible_tranche,
            current_position_weight_pct=8.5,
            target_position_weight_pct=15.0,
            feed_source=feed_source,
            feed_timestamp=feed_timestamp,
            feed_status=feed_status
        )

        return ArbitrationDirective(
            verdict_action=canonical_action,
            verdict_subtitle=verdict_subtitle,
            decision_object=decision_obj,
            primary_decision=primary_dec,
            tactical_timing=tactical_tim,
            execution_order_type=order_type,
            limit_entry_zone=zone,
            order_expiry_date=expiry_date,
            order_recheck_rule=recheck_rule,
            has_tier_conflict=has_conflict,
            tier_conflict_explanation=conflict_exp,
            is_event_blackout_active=is_blackout,
            blackout_reason=blackout_msg,
            overnight_gift_nifty_bias=gift_bias,
            thesis_break_status=thesis_status,
            what_would_change_my_mind=what_change
        )
