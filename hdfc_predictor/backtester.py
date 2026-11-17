"""
Historical Backtesting Engine for HDFC Bank.
Evaluates prediction model and news sentiment signals against historical share price data.
Compares strategy performance against Buy-and-Hold benchmark across key quant metrics.
"""
from dataclasses import dataclass
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd

from hdfc_predictor.config import settings
from hdfc_predictor.features import FeatureEngine
from hdfc_predictor.market_data import MarketDataProvider
from hdfc_predictor.model import HDFCPredictorModel, FEATURE_NAMES


@dataclass
class BacktestResult:
    start_date: str
    end_date: str
    total_trading_days: int
    benchmark_return_pct: float
    strategy_return_pct: float
    cagr_pct: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown_pct: float
    total_trades: int
    win_rate_pct: float
    profit_factor: float
    avg_trade_pnl_pct: float
    max_consecutive_wins: int
    max_consecutive_losses: int
    equity_curve: List[Dict[str, Any]]
    news_regime_performance: Dict[str, Any]


class Backtester:
    def __init__(self, symbol: str = settings.symbol):
        self.symbol = symbol
        self.market_data = MarketDataProvider(symbol=symbol)

    def run_backtest(
        self,
        period: str = "2y",
        train_ratio: float = 0.6,
        risk_free_rate: float = 0.065
    ) -> BacktestResult:
        """
        Executes out-of-sample backtest over historical period.
        """
        raw_df = self.market_data.get_historical_daily(period=period)
        if raw_df.empty or len(raw_df) < 100:
            raise ValueError(f"Insufficient historical data for {self.symbol} to backtest.")

        # Compute all technical features
        feature_df = FeatureEngine.build_feature_dataframe(raw_df)

        # Train/Test Split (Walk-forward out-of-sample testing)
        split_idx = int(len(feature_df) * train_ratio)
        train_df = feature_df.iloc[:split_idx].copy()
        test_df = feature_df.iloc[split_idx:].copy()

        # Fit model on training split
        model = HDFCPredictorModel()
        model.fit(train_df)

        # Run walk-forward simulation on test split
        capital = 100000.0  # Starting capital ₹1,00,000
        benchmark_capital = 100000.0
        equity_curve = []
        trades = []

        start_close = float(test_df["Close"].iloc[0])
        benchmark_shares = benchmark_capital / start_close

        prev_capital = capital
        consecutive_wins = 0
        consecutive_losses = 0
        max_c_wins = 0
        max_c_losses = 0

        # News regime trackers
        regime_trades = {"bullish_news": [], "bearish_news": [], "neutral_news": []}

        for i in range(len(test_df) - 1):
            row = test_df.iloc[i]
            next_row = test_df.iloc[i + 1]

            curr_date = test_df.index[i].strftime("%Y-%m-%d")
            curr_close = float(row["Close"])
            next_close = float(next_row["Close"])
            actual_next_return = (next_close - curr_close) / curr_close

            # Feature dictionary
            # Synthetic proxy sentiment calibrated with momentum and volatility shock for historical test
            sim_sentiment = float(np.clip(row["return_1d"] * 5.0 + (row["vol_ratio"] - 1.0) * 0.2, -1.0, 1.0))
            
            feat_dict = {feat: float(row[feat]) if feat in row else 0.0 for feat in FEATURE_NAMES}
            feat_dict["sentiment_score"] = sim_sentiment

            pred = model.predict(feat_dict, curr_close)
            action = pred["signal_action"]
            conf = pred["confidence_score"]

            trade_pnl_pct = 0.0
            trade_taken = False

            if "BUY" in action and conf >= settings.buy_threshold:
                # Long position taken at 2:00 PM / close, held to next close, minus 0.10% friction
                trade_pnl_pct = (actual_next_return * 100.0) - 0.10
                trade_taken = True
            elif "SELL" in action and conf >= settings.sell_threshold:
                # Sell / Short hedge or cash preservation, minus 0.10% friction
                trade_pnl_pct = (-actual_next_return * 100.0) - 0.10
                trade_taken = True
            else:
                trade_pnl_pct = 0.0

            if trade_taken:
                pnl_cash = prev_capital * (trade_pnl_pct / 100.0)
                capital += pnl_cash
                trades.append(trade_pnl_pct)

                if trade_pnl_pct > 0:
                    consecutive_wins += 1
                    consecutive_losses = 0
                    max_c_wins = max(max_c_wins, consecutive_wins)
                else:
                    consecutive_losses += 1
                    consecutive_wins = 0
                    max_c_losses = max(max_c_losses, consecutive_losses)

                if sim_sentiment > 0.15:
                    regime_trades["bullish_news"].append(trade_pnl_pct)
                elif sim_sentiment < -0.15:
                    regime_trades["bearish_news"].append(trade_pnl_pct)
                else:
                    regime_trades["neutral_news"].append(trade_pnl_pct)

            prev_capital = capital
            curr_benchmark = benchmark_shares * curr_close

            equity_curve.append({
                "date": curr_date,
                "strategy_equity": round(capital, 2),
                "benchmark_equity": round(curr_benchmark, 2),
                "action": action,
                "close": curr_close
            })

        # Calculate quant metrics
        end_close = float(test_df["Close"].iloc[-1])
        final_benchmark_return = ((end_close - start_close) / start_close) * 100.0
        final_strategy_return = ((capital - 100000.0) / 100000.0) * 100.0

        n_days = len(test_df)
        years = max(n_days / 252.0, 0.1)
        cagr = (((capital / 100000.0) ** (1.0 / years)) - 1.0) * 100.0

        # Daily returns for Sharpe
        df_eq = pd.DataFrame(equity_curve)
        df_eq["strat_ret"] = df_eq["strategy_equity"].pct_change().fillna(0)
        daily_rf = (1 + risk_free_rate) ** (1 / 252) - 1
        excess_returns = df_eq["strat_ret"] - daily_rf
        std_ret = df_eq["strat_ret"].std()
        sharpe = (excess_returns.mean() / (std_ret + 1e-9)) * np.sqrt(252) if std_ret > 0 else 0.0

        downside_ret = df_eq["strat_ret"][df_eq["strat_ret"] < 0].std()
        sortino = (excess_returns.mean() / (downside_ret + 1e-9)) * np.sqrt(252) if downside_ret > 0 else 0.0

        # Maximum Drawdown
        cum_max = df_eq["strategy_equity"].cummax()
        drawdown = (df_eq["strategy_equity"] - cum_max) / cum_max
        max_drawdown = float(drawdown.min() * 100.0)

        # Trade stats
        wins = [t for t in trades if t > 0]
        losses = [t for t in trades if t <= 0]
        win_rate = (len(wins) / len(trades) * 100.0) if trades else 0.0
        gross_profit = sum(wins) if wins else 0.0
        gross_loss = abs(sum(losses)) if losses else 0.0
        profit_factor = round(gross_profit / (gross_loss + 1e-6), 2)
        avg_trade_pnl = float(np.mean(trades)) if trades else 0.0

        # Regime performance breakdown
        def regime_stats(trade_list):
            if not trade_list:
                return {"trades": 0, "win_rate": 0.0, "avg_pnl": 0.0}
            w = sum(1 for x in trade_list if x > 0)
            return {
                "trades": len(trade_list),
                "win_rate": round((w / len(trade_list)) * 100.0, 1),
                "avg_pnl": round(float(np.mean(trade_list)), 2)
            }

        regime_perf = {
            "bullish_news": regime_stats(regime_trades["bullish_news"]),
            "bearish_news": regime_stats(regime_trades["bearish_news"]),
            "neutral_news": regime_stats(regime_trades["neutral_news"]),
        }

        return BacktestResult(
            start_date=test_df.index[0].strftime("%Y-%m-%d"),
            end_date=test_df.index[-1].strftime("%Y-%m-%d"),
            total_trading_days=n_days,
            benchmark_return_pct=round(final_benchmark_return, 2),
            strategy_return_pct=round(final_strategy_return, 2),
            cagr_pct=round(cagr, 2),
            sharpe_ratio=round(float(sharpe), 2),
            sortino_ratio=round(float(sortino), 2),
            max_drawdown_pct=round(max_drawdown, 2),
            total_trades=len(trades),
            win_rate_pct=round(win_rate, 2),
            profit_factor=profit_factor,
            avg_trade_pnl_pct=round(avg_trade_pnl, 2),
            max_consecutive_wins=max_c_wins,
            max_consecutive_losses=max_c_losses,
            equity_curve=equity_curve,
            news_regime_performance=regime_perf
        )
