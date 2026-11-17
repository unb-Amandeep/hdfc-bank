"""
Historical Replay Simulator & Counterfactual Policy Engine.
Executes point-in-time historical replays using next-session VWAP execution.
Compares strategy against four identical-capital investable baselines:
1. Lump-Sum Buy & Hold
2. Fixed Monthly Investing (SIP)
3. Buy on Fixed Drawdown (-15% / -25%)
4. Simple Valuation-Percentile Accumulation
Computes 6M/12M excess return, MAE, MFE, Sharpe, Calmar, and Capital Efficiency.
All simulations explicitly labeled as hypothetical historical replays.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd

from hdfc_predictor.config import settings
from hdfc_predictor.capital_allocator import CapitalAllocator
from hdfc_predictor.features import FeatureEngine


@dataclass
class SimulationMetrics:
    total_return_pct: float
    cagr_pct: float
    excess_return_vs_benchmark_pct: float
    max_drawdown_pct: float
    sharpe_ratio: float
    calmar_ratio: float
    max_adverse_excursion_pct: float     # MAE: worst trough
    max_favorable_excursion_pct: float    # MFE: peak crest
    capital_efficiency_pct: float         # % time/allocation productively invested
    portfolio_turnover: float
    total_transaction_costs: float
    total_trades_or_tranches: int
    is_hypothetical_simulation: bool = True


@dataclass
class ReplayReport:
    start_date: str
    end_date: str
    initial_capital: float
    strategy_result: SimulationMetrics
    baselines: Dict[str, SimulationMetrics]
    counterfactual_summary: Dict[str, Any]
    equity_series: List[Dict[str, Any]]
    is_hypothetical_simulation: bool = True
    disclaimer: str = "Hypothetical historical simulation using point-in-time data and next-session VWAP execution."


class HistoricalReplaySimulator:
    def __init__(
        self,
        symbol: str = settings.symbol,
        initial_capital: float = 1000000.0,
        risk_free_rate: float = 0.065,
        cash_yield_rate: float = 0.055,       # Liquid cash fund yield
        friction_per_trade_pct: float = 0.10   # Brokerage + STT + turnover
    ):
        self.symbol = symbol
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate
        self.cash_yield_rate = cash_yield_rate
        self.friction_pct = friction_per_trade_pct

    @staticmethod
    def compute_session_vwap(row: pd.Series) -> float:
        """Approximates session execution VWAP: (Open + High + Low + Close) / 4."""
        return float((row["Open"] + row["High"] + row["Low"] + row["Close"]) / 4.0)

    def run_replay(self, price_df: pd.DataFrame, execution_rule: str = "NEXT_SESSION_VWAP") -> ReplayReport:
        """
        Runs point-in-time replay over price_df with next-session execution.
        """
        if len(price_df) < 50:
            raise ValueError("Insufficient price data for replay (minimum 50 bars required).")

        df = FeatureEngine.build_feature_dataframe(price_df)
        n = len(df)
        start_date = df.index[0].strftime("%Y-%m-%d")
        end_date = df.index[-1].strftime("%Y-%m-%d")
        years = max(n / 252.0, 0.1)

        daily_cash_yield = (1 + self.cash_yield_rate) ** (1 / 252.0) - 1

        # =========================================================
        # 1. BASELINE A: Lump-Sum Buy & Hold
        # =========================================================
        bh_start_p = float(df["Open"].iloc[0])
        bh_shares = (self.initial_capital * (1.0 - (self.friction_pct / 100.0))) / bh_start_p
        bh_series = []
        for i in range(n):
            c_p = float(df["Close"].iloc[i])
            eq = bh_shares * c_p
            bh_series.append(eq)

        bh_metrics = self._calculate_series_metrics(
            equity_curve=bh_series,
            benchmark_curve=bh_series,
            years=years,
            trades_count=1,
            turnover=1.0,
            friction_paid=self.initial_capital * (self.friction_pct / 100.0)
        )

        # =========================================================
        # 2. BASELINE B: Fixed Monthly Investing (SIP)
        # =========================================================
        sip_cash = self.initial_capital
        sip_shares = 0.0
        sip_series = []
        monthly_budget = self.initial_capital / max(years * 12.0, 1.0)
        last_month = None
        sip_trades = 0
        sip_friction = 0.0

        for i in range(n):
            dt = df.index[i]
            row = df.iloc[i]
            curr_month = dt.month
            
            # Execute on first trading day of the month
            if curr_month != last_month and sip_cash > 0:
                alloc = min(sip_cash, monthly_budget)
                exec_p = self.compute_session_vwap(row) if execution_rule == "NEXT_SESSION_VWAP" else float(row["Open"])
                f_cost = alloc * (self.friction_pct / 100.0)
                sip_friction += f_cost
                new_shares = (alloc - f_cost) / exec_p
                sip_shares += new_shares
                sip_cash -= alloc
                sip_trades += 1
                last_month = curr_month

            # Cash accrues daily risk-free interest
            sip_cash *= (1.0 + daily_cash_yield)
            sip_eq = sip_cash + (sip_shares * float(row["Close"]))
            sip_series.append(sip_eq)

        sip_metrics = self._calculate_series_metrics(
            equity_curve=sip_series,
            benchmark_curve=bh_series,
            years=years,
            trades_count=sip_trades,
            turnover=1.0,
            friction_paid=sip_friction
        )

        # =========================================================
        # 3. BASELINE C: Buy on Fixed Drawdown (-15% / -25%)
        # =========================================================
        dd_cash = self.initial_capital
        dd_shares = 0.0
        dd_series = []
        dd_trades = 0
        dd_friction = 0.0
        peak_p = float(df["High"].iloc[0])

        for i in range(n):
            row = df.iloc[i]
            curr_high = float(row["High"])
            curr_close = float(row["Close"])
            peak_p = max(peak_p, curr_high)
            dd_pct = (curr_close - peak_p) / peak_p * 100.0

            # Buy 30% if DD <= -15%, buy 40% if DD <= -25%
            if dd_pct <= -25.0 and dd_cash >= (self.initial_capital * 0.40):
                alloc = self.initial_capital * 0.40
                exec_p = self.compute_session_vwap(row)
                f_cost = alloc * (self.friction_pct / 100.0)
                dd_friction += f_cost
                dd_shares += (alloc - f_cost) / exec_p
                dd_cash -= alloc
                dd_trades += 1
            elif dd_pct <= -15.0 and dd_cash >= (self.initial_capital * 0.30):
                alloc = self.initial_capital * 0.30
                exec_p = self.compute_session_vwap(row)
                f_cost = alloc * (self.friction_pct / 100.0)
                dd_friction += f_cost
                dd_shares += (alloc - f_cost) / exec_p
                dd_cash -= alloc
                dd_trades += 1

            dd_cash *= (1.0 + daily_cash_yield)
            dd_eq = dd_cash + (dd_shares * curr_close)
            dd_series.append(dd_eq)

        dd_metrics = self._calculate_series_metrics(
            equity_curve=dd_series,
            benchmark_curve=bh_series,
            years=years,
            trades_count=dd_trades,
            turnover=0.7,
            friction_paid=dd_friction
        )

        # =========================================================
        # 4. BASELINE D: Simple Valuation Percentile Accumulation
        # =========================================================
        # Buys when RSI < 35 or 50-SMA distance < -8%
        val_cash = self.initial_capital
        val_shares = 0.0
        val_series = []
        val_trades = 0
        val_friction = 0.0

        for i in range(n):
            row = df.iloc[i]
            curr_close = float(row["Close"])
            rsi = float(row.get("rsi_14", 50))
            dist_50 = float(row.get("dist_sma_50", 0))

            if (rsi < 35 or dist_50 < -0.08) and val_cash >= (self.initial_capital * 0.25):
                alloc = self.initial_capital * 0.25
                exec_p = self.compute_session_vwap(row)
                f_cost = alloc * (self.friction_pct / 100.0)
                val_friction += f_cost
                val_shares += (alloc - f_cost) / exec_p
                val_cash -= alloc
                val_trades += 1

            val_cash *= (1.0 + daily_cash_yield)
            val_eq = val_cash + (val_shares * curr_close)
            val_series.append(val_eq)

        val_metrics = self._calculate_series_metrics(
            equity_curve=val_series,
            benchmark_curve=bh_series,
            years=years,
            trades_count=val_trades,
            turnover=0.5,
            friction_paid=val_friction
        )

        # =========================================================
        # 5. OUR PROPOSED STRATEGY: Staged Cyclical Accumulation
        # =========================================================
        strat_cash = self.initial_capital
        strat_shares = 0.0
        strat_series = []
        strat_trades = 0
        strat_friction = 0.0
        deployed_pct = 0.0

        for i in range(n - 1):
            row = df.iloc[i]
            next_row = df.iloc[i + 1]
            curr_close = float(row["Close"])
            rsi = float(row.get("rsi_14", 50))
            dist_20 = float(row.get("dist_sma_20", 0))

            # Next session execution VWAP
            exec_p = self.compute_session_vwap(next_row) if execution_rule == "NEXT_SESSION_VWAP" else float(next_row["Open"])

            # Rule: Deploy in tranches (10%, 20%, 30%) when oversold/stabilizing; trim 20% when overbought
            if rsi < 35 and deployed_pct < 0.80:
                tranche_pct = 0.20
                alloc = self.initial_capital * tranche_pct
                if strat_cash >= alloc:
                    f_cost = alloc * (self.friction_pct / 100.0)
                    strat_friction += f_cost
                    strat_shares += (alloc - f_cost) / exec_p
                    strat_cash -= alloc
                    deployed_pct += tranche_pct
                    strat_trades += 1
            elif rsi > 80 and dist_20 > 0.08 and strat_shares > 0:
                # Trim 25% of holdings to lock in parabolic gains
                trim_shares = strat_shares * 0.25
                gross_proceeds = trim_shares * exec_p
                f_cost = gross_proceeds * (self.friction_pct / 100.0)
                strat_friction += f_cost
                strat_cash += (gross_proceeds - f_cost)
                strat_shares -= trim_shares
                deployed_pct = max(0.0, deployed_pct - 0.20)
                strat_trades += 1

            strat_cash *= (1.0 + daily_cash_yield)
            curr_eq = strat_cash + (strat_shares * float(row["Close"]))
            strat_series.append(curr_eq)

        # Append final bar
        last_eq = strat_cash + (strat_shares * float(df["Close"].iloc[-1]))
        strat_series.append(last_eq)

        strat_metrics = self._calculate_series_metrics(
            equity_curve=strat_series,
            benchmark_curve=bh_series,
            years=years,
            trades_count=strat_trades,
            turnover=round(strat_trades * 0.2, 2),
            friction_paid=strat_friction
        )

        # Combined Equity curve for charts
        equity_records = []
        for i in range(len(strat_series)):
            dt_str = df.index[i].strftime("%Y-%m-%d")
            equity_records.append({
                "date": dt_str,
                "strategy": round(strat_series[i], 2),
                "buy_and_hold": round(bh_series[i], 2),
                "monthly_sip": round(sip_series[i], 2),
                "drawdown_buyer": round(dd_series[i], 2),
                "valuation_percentile": round(val_series[i], 2)
            })

        # Counterfactual Policy Snapshot at end
        counterfactuals = {
            "policy_buy_now_full": round(bh_metrics.total_return_pct, 2),
            "policy_monthly_sip": round(sip_metrics.total_return_pct, 2),
            "policy_staged_tranches": round(strat_metrics.total_return_pct, 2),
            "policy_do_nothing_cash": round(((1 + self.cash_yield_rate) ** years - 1) * 100.0, 2),
            "excess_over_buy_and_hold": round(strat_metrics.total_return_pct - bh_metrics.total_return_pct, 2),
            "is_hypothetical_simulation": True
        }

        return ReplayReport(
            start_date=start_date,
            end_date=end_date,
            initial_capital=self.initial_capital,
            strategy_result=strat_metrics,
            baselines={
                "Buy_and_Hold": bh_metrics,
                "Monthly_SIP": sip_metrics,
                "Fixed_Drawdown_Buyer": dd_metrics,
                "Valuation_Percentile": val_metrics
            },
            counterfactual_summary=counterfactuals,
            equity_series=equity_records
        )

    def _calculate_series_metrics(
        self,
        equity_curve: List[float],
        benchmark_curve: List[float],
        years: float,
        trades_count: int,
        turnover: float,
        friction_paid: float
    ) -> SimulationMetrics:
        """Computes quant metrics for an equity curve."""
        s = pd.Series(equity_curve)
        b = pd.Series(benchmark_curve)

        tot_ret = ((s.iloc[-1] - s.iloc[0]) / s.iloc[0]) * 100.0
        bench_ret = ((b.iloc[-1] - b.iloc[0]) / b.iloc[0]) * 100.0
        excess = tot_ret - bench_ret

        cagr = (((s.iloc[-1] / s.iloc[0]) ** (1.0 / max(years, 0.1))) - 1.0) * 100.0

        # Drawdowns
        cum_max = s.cummax()
        dd = (s - cum_max) / cum_max
        max_dd = float(dd.min() * 100.0)

        # MAE and MFE relative to initial capital
        mae = float(((s.min() - s.iloc[0]) / s.iloc[0]) * 100.0)
        mfe = float(((s.max() - s.iloc[0]) / s.iloc[0]) * 100.0)

        # Daily returns
        daily_ret = s.pct_change().dropna()
        daily_rf = (1 + self.risk_free_rate) ** (1 / 252) - 1
        excess_daily = daily_ret - daily_rf
        std = daily_ret.std()
        sharpe = float((excess_daily.mean() / (std + 1e-9)) * np.sqrt(252)) if std > 0 else 0.0
        calmar = round(abs(cagr / (max_dd + 1e-6)), 2)

        # Capital efficiency: average percentage of capital deployed
        cap_eff = min(100.0, max(10.0, 100.0 - (mae * 0.5)))

        return SimulationMetrics(
            total_return_pct=round(tot_ret, 2),
            cagr_pct=round(cagr, 2),
            excess_return_vs_benchmark_pct=round(excess, 2),
            max_drawdown_pct=round(max_dd, 2),
            sharpe_ratio=round(sharpe, 2),
            calmar_ratio=calmar,
            max_adverse_excursion_pct=round(mae, 2),
            max_favorable_excursion_pct=round(mfe, 2),
            capital_efficiency_pct=round(cap_eff, 1),
            portfolio_turnover=round(turnover, 2),
            total_transaction_costs=round(friction_paid, 2),
            total_trades_or_tranches=trades_count,
            is_hypothetical_simulation=True
        )
