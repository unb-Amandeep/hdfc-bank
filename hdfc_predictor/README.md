# 🏦 HDFC Bank Daily AI Price Predictor & Backtesting System

An autonomous quantitative and news sentiment decision system for **HDFC Bank Limited** (`HDFCBANK.NS` / `HDB`).

Every trading day at **2:00 PM IST** (1.5 hours prior to market close at 3:30 PM IST), the engine analyzes intraday price action, technical indicators, and real-time banking news sentiment to deliver an actionable trade recommendation (**BUY MORE**, **SELL / TRIM**, or **HOLD**).

The system features an autonomous **self-improving feedback loop** that reconciles past predictions against verified market closes, adjusts dynamic confidence thresholds, and retrains its models over time.

---

## 🚀 Key Features

1. **Backtesting Engine Against News & Price Data**:
   - Tests ML directional signals and sentiment regimes over 1-year, 2-year, or 3-year historical horizons.
   - Evaluates performance against a Buy-and-Hold benchmark across quantitative metrics: **Total Return %**, **CAGR**, **Sharpe Ratio**, **Sortino Ratio**, **Max Drawdown**, **Profit Factor**, and **Win Rate %**.
   - Breaks down strategy performance across **Bullish News**, **Bearish News**, and **Neutral News** regimes.

2. **Daily 2:00 PM (IST) Trade Recommendation**:
   - Delivers clear signals: `STRONG BUY`, `BUY MORE`, `HOLD`, `SELL / TRIM`, or `STRONG SELL`.
   - Computes dynamic ATR-based **Target Price** and **Stop-Loss Price**.
   - Provides factor attribution: RSI, MACD momentum, Bollinger Bands, Moving Average divergence, and news catalysts.
   - Delivers immediate **native macOS banner notifications** with audio alerts.

3. **Live Financial Data Ingestion (Free APIs)**:
   - Works **100% out of the box with zero API keys required** via `yfinance` real-time fast info and live Google News RSS feeds.
   - Supports free tier API keys for deeper sentiment and cross-market validation:
     - **Finnhub.io** (Free tier: 60 calls/min for real-time quotes & company news).
     - **Alpha Vantage** (Free tier: 25 calls/day for News Sentiment API & indicators).

4. **Self-Improving Feedback Loop ("Improves Everyday")**:
   - Persistent SQLite brain (`data/hdfc_brain.db`).
   - Every day before market close, the engine checks previous predictions and compares them against the verified market close.
   - Reconciles wins vs losses, tracks rolling 7-day and 30-day accuracy.
   - Dynamically calibrates trade confidence thresholds (tightens during volatile whipsaw regimes, optimizes during high-conviction regimes).

5. **Interactive Web Dashboard**:
   - Reactive dark-mode dashboard with Chart.js equity curve visualizer, live price streaming, today's 2:00 PM conviction card, news stream, and prediction verification history.

6. **Automated Background Scheduling**:
   - Native macOS **LaunchAgent** runs silently in the background at 14:00 IST Monday through Friday, even if the terminal is closed.

---

## 🛠️ Quick Start & CLI Usage

From the project root:

```bash
# 1. Run Today's 2:00 PM Signal Right Now
./.venv/bin/python -m hdfc_predictor signal

# 2. Run Historical Backtest (1y, 2y, or 3y)
./.venv/bin/python -m hdfc_predictor backtest --period 2y

# 3. Inspect Self-Improving Brain & Outcome Reconciliation
./.venv/bin/python -m hdfc_predictor learn

# 4. Check or Manage macOS 2:00 PM Background Schedule
./.venv/bin/python -m hdfc_predictor schedule
./.venv/bin/python -m hdfc_predictor schedule --install-launchd

# 5. Launch Interactive Web Dashboard
./.venv/bin/python -m hdfc_predictor dashboard --port 8501
```

---

## 📁 System Architecture

### Phase 1: Point-in-Time Data Foundation & Abstention
- **Point-in-Time Data Tables**: `raw_observations` (metric lineage, sources, revisions, as-of dates), `corporate_actions` (splits, bonuses, mergers), `data_quality_log`.
- **Corporate Action Adjustments**: Consistent backwards adjustment across per-share metrics (EPS, BVPS) and price feeds.
- **ADR Normalization Engine**: Configurable ratio (default 3.0 shares/ADS), USD/INR FX alignment, US/India holiday offset tracking.
- **Data Quality Gates**: Freshness validation, schema integrity, and raw bar indicator recomputation (cross-checking RSI and 20-SMA distance).
- **Abstention Engine**: Commands unequivocal `ABSTAIN` on data drift, source conflict (>2.5%), or out-of-distribution regime; strictly blocks capital allocation (0% deployed).

### Phase 2: Historical Replay Simulator & Investable Baselines
- **Next-Session VWAP Execution**: Replays history using strictly point-in-time signals with next-session execution rule $(O+H+L+C)/4$ plus institutional friction (0.10%).
- **Identical-Capital Baselines**: Benchmarks strategy against Lump-Sum Buy & Hold, Monthly SIP, Buy on Fixed Drawdown (-15%/-25%), and Simple Valuation-Percentile Accumulation.
- **Counterfactual Policies**: Measures trade-offs between "Buy Now Full", "Monthly SIP", "Staged Tranches", and "Hold Cash".
- **Advanced Quant Metrics**: Evaluates MAE (Maximum Adverse Excursion), MFE (Maximum Favorable Excursion), Sharpe, Calmar, Capital Efficiency, and net transaction friction. All outputs marked as hypothetical simulations.



```
hdfc_predictor/
├── config.py           # Configuration, tickers, thresholds, and paths
├── database.py         # SQLite persistence layer (predictions, outcomes, metrics)
├── market_data.py      # Real-time quotes & historical OHLCV data engine
├── news_engine.py      # Google News RSS, Finnhub, Alpha Vantage & NLP sentiment
├── features.py         # Technical indicators (RSI, MACD, Bollinger Bands, ATR, MAs)
├── model.py            # Gradient Boosting classifier, Stop-Loss & Target logic
├── learner.py          # Continuous feedback loop & adaptive threshold calibration
├── backtester.py       # Historical simulation engine & quant metrics
├── signal_generator.py # 2:00 PM pipeline coordinator & macOS notification dispatcher
├── scheduler.py        # macOS LaunchAgent & daemon scheduler
├── dashboard.py        # Local web UI & REST endpoints (port 8501)
├── cli.py              # CLI entry point
├── data/
│   ├── hdfc_brain.db   # SQLite database tracking daily predictions & outcomes
│   ├── hdfc_model.pkl  # Trained ML model weights
│   └── hdfc_scaler.pkl # Feature scaler
└── reports/
    └── latest_signal.md # Markdown daily summary report
```

---

## ⚙️ Configuration & API Keys (Optional)

Create a `.env` file in the workspace root if you wish to add free API keys:

```env
FINNHUB_API_KEY=your_free_finnhub_key
ALPHAVANTAGE_API_KEY=your_free_alphavantage_key
```
*(If omitted, the system seamlessly uses yfinance and Google News RSS feeds with zero configuration needed).*
