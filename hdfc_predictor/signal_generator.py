"""
Daily 2:00 PM Signal Generator & Automation for HDFC Bank.
Runs automated self-improvement, fetches live 2:00 PM market quote & news sentiment,
generates actionable trade signal (BUY MORE / SELL / HOLD), saves prediction to database,
and delivers native macOS desktop notifications.
"""
from datetime import datetime, date
import json
import os
import subprocess
from typing import Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hdfc_predictor.config import settings
from hdfc_predictor.database import init_db, save_prediction
from hdfc_predictor.market_data import MarketDataProvider
from hdfc_predictor.news_engine import NewsEngine
from hdfc_predictor.features import FeatureEngine
from hdfc_predictor.model import HDFCPredictorModel
from hdfc_predictor.learner import FeedbackLearner

console = Console()


class SignalGenerator:
    def __init__(self):
        init_db()
        self.market_data = MarketDataProvider()
        self.news_engine = NewsEngine()
        self.learner = FeedbackLearner()
        self.model = HDFCPredictorModel()

    def run_daily_signal(self, force: bool = False) -> Dict[str, Any]:
        """
        Executes complete 2:00 PM pipeline:
        1. Reconcile past predictions & self-improve
        2. Fetch real-time market data
        3. Ingest latest news and compute sentiment
        4. Calculate technical indicators & run ML model
        5. Persist prediction and trigger notifications
        """
        # Step 1: Self-improvement feedback loop
        reconciled = self.learner.reconcile_pending_predictions()
        calibration_stats = self.learner.update_model_and_recalibrate()

        # Step 2: Fetch Live Quote
        quote = self.market_data.get_live_quote()
        curr_price = quote.get("current_price")
        if curr_price is None or curr_price <= 0:
            raise RuntimeError(f"Unable to fetch valid live quote for {settings.symbol}")

        # Step 3: Ingest news & compute sentiment
        news_data = self.news_engine.get_latest_news_and_sentiment()
        sentiment_score = news_data["overall_sentiment"]
        top_headlines = [a["title"] for a in news_data.get("top_articles", [])[:3]]
        headline_summary = " | ".join(top_headlines) if top_headlines else "No major news headlines detected."

        # Step 4: Extract features & predict
        hist_df = self.market_data.get_historical_daily(period="1y")
        
        # Ensure model is initialized or fit
        if self.model.model is None:
            enriched_df = FeatureEngine.build_feature_dataframe(hist_df)
            self.model.fit(enriched_df)

        feat_vector = FeatureEngine.get_latest_feature_vector(hist_df, sentiment_score=sentiment_score)
        prediction = self.model.predict(feat_vector, curr_price)

        today_str = datetime.now().strftime("%Y-%m-%d")
        now_iso = datetime.now().isoformat()

        # Step 5: Save prediction to SQLite database
        record = {
            "timestamp": now_iso,
            "date": today_str,
            "symbol": settings.symbol,
            "price_at_signal": curr_price,
            "day_open": quote.get("day_open", curr_price),
            "day_high": quote.get("day_high", curr_price),
            "day_low": quote.get("day_low", curr_price),
            "signal_action": prediction["signal_action"],
            "confidence_score": prediction["confidence_score"],
            "sentiment_score": sentiment_score,
            "rsi_14": feat_vector["rsi_14"],
            "macd_val": feat_vector["macd"],
            "macd_signal": feat_vector["macd_signal"],
            "stop_loss": prediction["stop_loss"],
            "target_price": prediction["target_price"],
            "headline_sample": headline_summary,
            "reasoning": prediction["summary_reasoning"],
            "features_json": json.dumps(feat_vector)
        }
        pred_id = save_prediction(record)

        # Step 6: Dispatch notifications and save report
        self.send_desktop_notification(prediction, curr_price)
        self.save_markdown_report(quote, prediction, news_data, feat_vector, calibration_stats)

        return {
            "prediction_id": pred_id,
            "quote": quote,
            "prediction": prediction,
            "news": news_data,
            "reconciled_count": len(reconciled),
            "calibration": calibration_stats
        }

    def send_desktop_notification(self, prediction: Dict[str, Any], current_price: float):
        """Dispatches native macOS banner notification with chime."""
        action = prediction["signal_action"]
        conf = int(prediction["confidence_score"] * 100)
        target = prediction["target_price"]
        stop = prediction["stop_loss"]

        title = f"HDFC Bank 2:00 PM Signal: {action}"
        message = f"Price: ₹{current_price} | Conf: {conf}% | Target: ₹{target} | Stop: ₹{stop}"
        
        sound = "Hero" if "BUY" in action else ("Basso" if "SELL" in action else "Purr")
        apple_script = f'display notification "{message}" with title "{title}" sound name "{sound}"'
        try:
            subprocess.run(["osascript", "-e", apple_script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

    def save_markdown_report(
        self,
        quote: Dict[str, Any],
        prediction: Dict[str, Any],
        news: Dict[str, Any],
        features: Dict[str, Any],
        calibration: Dict[str, Any]
    ):
        """Generates formatted daily report in markdown."""
        action = prediction["signal_action"]
        color = "🟢" if "BUY" in action else ("🔴" if "SELL" in action else "🟡")
        
        content = f"""# {color} HDFC Bank Daily 2:00 PM Signal Report
**Date & Time**: {datetime.now().strftime("%A, %d %B %Y at %I:%M %p IST")}  
**Symbol**: `{settings.symbol}` | **Data Source**: {quote.get('source', 'Live API')}

---

## ⚡ Recommended Action: **{action}**
- **Current Share Price**: **₹{quote['current_price']}** ({quote.get('change_pct', 0.0):+.2f}%)
- **Signal Confidence**: **{prediction['confidence_score'] * 100:.1f}%**
- **Recommended Target**: **₹{prediction['target_price']}**
- **Recommended Stop-Loss**: **₹{prediction['stop_loss']}**
- **Risk / Reward**: 1 : {settings.default_target_atr_mult / settings.default_stop_loss_atr_mult:.2f}

---

## 📊 Technical Indicators (Snapshot at 2:00 PM)
| Indicator | Value | Interpretation |
| :--- | :--- | :--- |
| **RSI (14)** | `{features['rsi_14']:.2f}` | {"Oversold (Bullish)" if features['rsi_14'] < 35 else ("Overbought (Bearish)" if features['rsi_14'] > 65 else "Neutral")} |
| **MACD / Signal** | `{features['macd']:.2f}` / `{features['macd_signal']:.2f}` | {"Bullish Crossover" if features['macd'] > features['macd_signal'] else "Bearish Pressure"} |
| **Bollinger %B** | `{features['bb_pct_b']:.2f}` | {"Near lower band (Support)" if features['bb_pct_b'] < 0.2 else ("Near upper band (Resistance)" if features['bb_pct_b'] > 0.8 else "Mid-band")} |
| **ATR (14)** | `₹{features['atr_14']:.2f}` | Daily Volatility Benchmark |
| **20-Day SMA Dist**| `{features['dist_sma_20'] * 100:+.2f}%` | Short-term trend deviation |

---

## 📰 News & Sentiment Breakdown
- **Overall Sentiment Index**: `{news['overall_sentiment']:+.2f}` ({news['sentiment_label']})
- **News Volume Tracked**: {news['news_count']} articles ({news['bullish_count']} Bullish, {news['bearish_count']} Bearish, {news['neutral_count']} Neutral)

### Top Headlines Analyzed:
"""
        for art in news.get("top_articles", [])[:5]:
            emoji = "🟢" if art.get("sentiment_label") == "BULLISH" else ("🔴" if art.get("sentiment_label") == "BEARISH" else "⚪")
            content += f"- {emoji} **{art['title']}** ({art.get('source', 'News')}) [Sentiment: {art.get('sentiment_score', 0.0):+.2f}]\n"

        content += f"""
---

## 🧠 Continuous Learning & Self-Improvement
- **Learning Iterations**: {calibration.get('total_samples', 0)} verified samples
- **Rolling Accuracy**: {calibration.get('rolling_7d_accuracy', 0.0)}%
- **Threshold Calibration**: Buy @ `{calibration.get('calibrated_buy_threshold', settings.buy_threshold)}` | Sell @ `{calibration.get('calibrated_sell_threshold', settings.sell_threshold)}`
- **Notes**: {calibration.get('notes', 'Normal operational regime')}

---
*Generated automatically by HDFC Predictor at 2:00 PM IST.*
"""
        with open(settings.daily_report_path, "w") as f:
            f.write(content)

    def print_signal_console(self, result: Dict[str, Any]):
        """Prints a rich terminal display."""
        quote = result["quote"]
        pred = result["prediction"]
        news = result["news"]

        action = pred["signal_action"]
        color = "green bold" if "BUY" in action else ("red bold" if "SELL" in action else "yellow bold")

        table = Table(title=f"HDFC Bank 2:00 PM Trade Signal ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="white")

        table.add_row("Action", f"[{color}]{action}[/{color}]")
        table.add_row("Current Price", f"₹{quote['current_price']} ({quote.get('change_pct', 0.0):+.2f}%)")
        table.add_row("Confidence", f"{pred['confidence_score'] * 100:.1f}%")
        table.add_row("Target Price", f"₹{pred['target_price']}")
        table.add_row("Stop Loss", f"₹{pred['stop_loss']}")
        table.add_row("News Sentiment", f"{news['overall_sentiment']:+.2f} ({news['sentiment_label']})")
        table.add_row("Key Factors", pred["summary_reasoning"])

        console.print(table)
