"""
Market Data Provider for HDFC Bank (HDFCBANK.NS / HDB).
Fetches historical daily prices and real-time intraday quotes using free APIs
(yfinance, Finnhub, Alpha Vantage, and direct web endpoints).
"""
from datetime import datetime, timedelta
import json
from typing import Dict, Any, Optional, Tuple
import urllib.request
import urllib.parse
import pandas as pd
import numpy as np

from hdfc_predictor.config import settings


class MarketDataProvider:
    def __init__(self, symbol: str = settings.symbol):
        self.symbol = symbol
        self.backup_symbol = settings.backup_symbol
        self.finnhub_key = settings.finnhub_api_key
        self.alpha_key = settings.alphavantage_api_key

    def get_alphavantage_quote(self, symbol: str = "HDB") -> Optional[Dict[str, Any]]:
        """
        Fetches live Global Quote from Alpha Vantage for HDFC Bank ADR (HDB).
        Provides international institutional price confirmation.
        """
        if not self.alpha_key:
            return None
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_key}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "HDFC-Predictor/1.0"})
            with urllib.request.urlopen(req, timeout=8) as res:
                data = json.loads(res.read().decode())
                gq = data.get("Global Quote", {})
                if gq and "05. price" in gq:
                    price = float(gq["05. price"])
                    chg_pct = float(gq.get("10. change percent", "0.0%").replace("%", ""))
                    return {
                        "symbol": symbol,
                        "price": round(price, 2),
                        "open": round(float(gq.get("02. open", price)), 2),
                        "high": round(float(gq.get("03. high", price)), 2),
                        "low": round(float(gq.get("04. low", price)), 2),
                        "change_pct": round(chg_pct, 2),
                        "volume": int(gq.get("06. volume", 0)),
                        "latest_day": gq.get("07. latest trading day"),
                        "source": "Alpha Vantage (HDB)"
                    }
        except Exception:
            pass
        return None

    def get_live_quote(self) -> Dict[str, Any]:
        """
        Fetches the latest real-time / delayed quote for HDFC Bank.
        Combines yfinance fast_info and Finnhub real-time API if available.
        """
        quote_data = {
            "symbol": self.symbol,
            "timestamp": datetime.now().isoformat(),
            "current_price": None,
            "day_open": None,
            "day_high": None,
            "day_low": None,
            "previous_close": None,
            "change": None,
            "change_pct": None,
            "volume": None,
            "adr_quote": self.get_alphavantage_quote("HDB"),
            "source": "none"
        }

        # 1. Try Finnhub real-time if API key configured
        if self.finnhub_key:
            try:
                # Finnhub tracks HDB (NYSE ADR) or HDFCBANK.NS
                target_sym = self.backup_symbol if not self.symbol.endswith(".NS") else self.symbol
                url = f"https://finnhub.io/api/v1/quote?symbol={target_sym}&token={self.finnhub_key}"
                req = urllib.request.Request(url, headers={"User-Agent": "HDFC-Predictor/1.0"})
                with urllib.request.urlopen(req, timeout=5) as res:
                    data = json.loads(res.read().decode())
                    if data.get("c", 0) > 0:
                        c = float(data["c"])
                        pc = float(data["pc"])
                        quote_data.update({
                            "current_price": round(c, 2),
                            "day_open": round(float(data.get("o", c)), 2),
                            "day_high": round(float(data.get("h", c)), 2),
                            "day_low": round(float(data.get("l", c)), 2),
                            "previous_close": round(pc, 2),
                            "change": round(c - pc, 2),
                            "change_pct": round(((c - pc) / pc) * 100, 2),
                            "source": f"Finnhub ({target_sym})"
                        })
                        return quote_data
            except Exception:
                pass

        # 2. Try yfinance (Free, no key needed)
        try:
            import yfinance as yf
            ticker = yf.Ticker(self.symbol)
            fast_info = ticker.fast_info
            
            curr = fast_info.last_price
            prev_close = fast_info.previous_close
            open_price = fast_info.open
            high_price = fast_info.day_high
            low_price = fast_info.day_low
            vol = fast_info.last_volume

            if curr is not None and not np.isnan(curr) and curr > 0:
                chg = curr - prev_close if prev_close else 0.0
                chg_pct = (chg / prev_close) * 100 if prev_close else 0.0
                quote_data.update({
                    "current_price": round(float(curr), 2),
                    "day_open": round(float(open_price or curr), 2),
                    "day_high": round(float(high_price or curr), 2),
                    "day_low": round(float(low_price or curr), 2),
                    "previous_close": round(float(prev_close or curr), 2),
                    "change": round(float(chg), 2),
                    "change_pct": round(float(chg_pct), 2),
                    "volume": int(vol) if vol else 0,
                    "source": "Yahoo Finance (HDFCBANK.NS)"
                })
                return quote_data
        except Exception:
            pass

        # 3. Fallback: historical recent bar if fast_info fails
        try:
            import yfinance as yf
            df = yf.download(self.symbol, period="5d", interval="1d", progress=False)
            if not df.empty:
                last_row = df.iloc[-1]
                prev_row = df.iloc[-2] if len(df) > 1 else last_row
                c = float(last_row["Close"].iloc[0] if hasattr(last_row["Close"], "iloc") else last_row["Close"])
                pc = float(prev_row["Close"].iloc[0] if hasattr(prev_row["Close"], "iloc") else prev_row["Close"])
                o = float(last_row["Open"].iloc[0] if hasattr(last_row["Open"], "iloc") else last_row["Open"])
                h = float(last_row["High"].iloc[0] if hasattr(last_row["High"], "iloc") else last_row["High"])
                l = float(last_row["Low"].iloc[0] if hasattr(last_row["Low"], "iloc") else last_row["Low"])
                v = int(last_row["Volume"].iloc[0] if hasattr(last_row["Volume"], "iloc") else last_row["Volume"])
                quote_data.update({
                    "current_price": round(c, 2),
                    "day_open": round(o, 2),
                    "day_high": round(h, 2),
                    "day_low": round(l, 2),
                    "previous_close": round(pc, 2),
                    "change": round(c - pc, 2),
                    "change_pct": round(((c - pc) / pc) * 100, 2),
                    "volume": v,
                    "source": "Yahoo Finance (Historical bar)"
                })
                return quote_data
        except Exception as e:
            pass

        return quote_data

    def get_historical_daily(self, period: str = "2y") -> pd.DataFrame:
        """
        Fetches historical daily OHLCV dataframe.
        """
        try:
            import yfinance as yf
            df = yf.download(self.symbol, period=period, interval="1d", progress=False)
            if df.empty:
                # Fallback to NYSE ticker HDB if NS fails
                df = yf.download(self.backup_symbol, period=period, interval="1d", progress=False)
                
            # Flatten MultiIndex columns if present in newer yfinance
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
                
            df.dropna(inplace=True)
            return df
        except Exception as e:
            raise RuntimeError(f"Failed to fetch historical market data: {e}")

    def get_intraday_data(self, days: int = 5, interval: str = "15m") -> pd.DataFrame:
        """
        Fetches intraday bars (useful for examining 2:00 PM momentum).
        """
        try:
            import yfinance as yf
            df = yf.download(self.symbol, period=f"{days}d", interval=interval, progress=False)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = [col[0] for col in df.columns]
            df.dropna(inplace=True)
            return df
        except Exception:
            return pd.DataFrame()
