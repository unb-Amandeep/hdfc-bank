"""
Configuration settings for HDFC Bank Daily Price Predictor & Backtesting System.
"""
from dataclasses import dataclass, field
import os
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("HDFC_DATA_DIR", BASE_DIR / "data"))
LOGS_DIR = BASE_DIR / "logs"
REPORTS_DIR = BASE_DIR / "reports"

# Ensure runtime directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

# Load optional .env file if present
ENV_FILE = BASE_DIR.parent / ".env"
if ENV_FILE.exists():
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip("'\""))


@dataclass
class Settings:
    # Ticker Settings
    symbol: str = "HDFCBANK.NS"  # Primary NSE ticker
    backup_symbol: str = "HDB"   # NYSE ADR for cross-border confirmation
    benchmark_symbol: str = "^NSEBANK"  # Nifty Bank Index benchmark
    company_name: str = "HDFC Bank"
    
    # Time and Scheduling
    market_timezone: str = "Asia/Kolkata"
    daily_signal_time: str = "14:00"  # 2:00 PM IST (before 3:30 PM close)
    market_open_time: str = "09:15"
    market_close_time: str = "15:30"
    
    # Financial API Keys (Free keys supported)
    # 1. Finnhub (Free tier: 60 req/min, provides real-time quotes & news)
    finnhub_api_key: Optional[str] = os.getenv("FINNHUB_API_KEY", "")
    
    # 2. Alpha Vantage (Free tier: 25 req/day, provides News Sentiment API & indicators)
    alphavantage_api_key: Optional[str] = os.getenv("ALPHAVANTAGE_API_KEY", "")
    
    # 3. NewsAPI (Optional)
    news_api_key: Optional[str] = os.getenv("NEWS_API_KEY", "")
    
    # Strategy & Thresholds
    buy_threshold: float = 0.55       # >55% probability -> BUY MORE
    strong_buy_threshold: float = 0.68 # >68% probability -> STRONG BUY
    sell_threshold: float = 0.45      # <45% probability -> SELL / REDUCE
    strong_sell_threshold: float = 0.32# <32% probability -> STRONG SELL
    
    # Risk Management Defaults
    default_stop_loss_atr_mult: float = 1.5
    default_target_atr_mult: float = 2.5
    
    # Paths
    db_path: Path = DATA_DIR / "hdfc_brain.db"
    model_path: Path = DATA_DIR / "hdfc_model.pkl"
    scaler_path: Path = DATA_DIR / "hdfc_scaler.pkl"
    learning_stats_path: Path = DATA_DIR / "learning_history.json"
    daily_report_path: Path = REPORTS_DIR / "latest_signal.md"

settings = Settings()
