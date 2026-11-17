"""
Feature Engineering for HDFC Bank Daily Price Movement.
Computes technical indicators (RSI, MACD, Bollinger Bands, ATR, Moving Averages)
and integrates sentiment features for the predictive model.
"""
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple


class FeatureEngine:
    @staticmethod
    def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta = series.diff()
        gain = (delta.where(delta > 0, 0.0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0.0)).rolling(window=period).mean()
        rs = gain / (loss + 1e-9)
        rsi = 100 - (100 / (1 + rs))
        return rsi

    @staticmethod
    def compute_macd(series: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        ema_fast = series.ewm(span=fast, adjust=False).mean()
        ema_slow = series.ewm(span=slow, adjust=False).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal, adjust=False).mean()
        macd_hist = macd - macd_signal
        return macd, macd_signal, macd_hist

    @staticmethod
    def compute_bollinger_bands(series: pd.Series, window: int = 20, num_std: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series, pd.Series]:
        sma = series.rolling(window=window).mean()
        std = series.rolling(window=window).std()
        upper = sma + (std * num_std)
        lower = sma - (std * num_std)
        pct_b = (series - lower) / (upper - lower + 1e-9)
        bandwidth = (upper - lower) / (sma + 1e-9)
        return upper, lower, pct_b, bandwidth

    @staticmethod
    def compute_atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        high = df["High"]
        low = df["Low"]
        close = df["Close"]
        prev_close = close.shift(1)
        
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr

    @classmethod
    def build_feature_dataframe(cls, df: pd.DataFrame) -> pd.DataFrame:
        """
        Takes raw daily OHLCV dataframe and enriches it with all predictive features.
        """
        data = df.copy()
        close = data["Close"]
        open_p = data["Open"]
        high = data["High"]
        low = data["Low"]
        vol = data["Volume"]

        # 1. Technical Indicators
        data["rsi_14"] = cls.compute_rsi(close, 14)
        macd, macd_sig, macd_hist = cls.compute_macd(close, 12, 26, 9)
        data["macd"] = macd
        data["macd_signal"] = macd_sig
        data["macd_hist"] = macd_hist

        upper, lower, pct_b, bandwidth = cls.compute_bollinger_bands(close, 20, 2.0)
        data["bb_pct_b"] = pct_b
        data["bb_bandwidth"] = bandwidth

        data["atr_14"] = cls.compute_atr(data, 14)

        # 2. Moving Averages
        data["sma_20"] = close.rolling(20).mean()
        data["sma_50"] = close.rolling(50).mean()
        data["ema_9"] = close.ewm(span=9, adjust=False).mean()
        data["ema_21"] = close.ewm(span=21, adjust=False).mean()

        data["dist_sma_20"] = (close - data["sma_20"]) / (data["sma_20"] + 1e-9)
        data["dist_sma_50"] = (close - data["sma_50"]) / (data["sma_50"] + 1e-9)
        data["ema_9_21_cross"] = np.where(data["ema_9"] > data["ema_21"], 1.0, -1.0)

        # 3. Volume Trends
        vol_sma_20 = vol.rolling(20).mean()
        data["vol_ratio"] = vol / (vol_sma_20 + 1e-9)

        # 4. Momentum & Candlestick Metrics
        data["return_1d"] = close.pct_change(1)
        data["return_3d"] = close.pct_change(3)
        data["return_5d"] = close.pct_change(5)

        range_hl = (high - low).replace(0, 1e-9)
        data["body_ratio"] = (close - open_p) / range_hl
        data["upper_shadow_ratio"] = (high - np.maximum(close, open_p)) / range_hl
        data["lower_shadow_ratio"] = (np.minimum(close, open_p) - low) / range_hl

        # 5. Target variable for training (Next Day Return & Next Day Direction)
        data["next_close"] = close.shift(-1)
        data["target_return"] = (data["next_close"] - close) / close
        data["target_direction"] = (data["target_return"] > 0).astype(int)

        data.dropna(subset=["rsi_14", "macd", "sma_50", "atr_14"], inplace=True)
        return data

    @classmethod
    def get_latest_feature_vector(cls, df: pd.DataFrame, sentiment_score: float = 0.0) -> Dict[str, Any]:
        """
        Extracts current state feature snapshot for live inference.
        """
        enriched = cls.build_feature_dataframe(df)
        if enriched.empty:
            raise ValueError("Dataframe too short to compute technical indicators.")
            
        latest = enriched.iloc[-1]
        
        feature_dict = {
            "rsi_14": float(latest["rsi_14"]),
            "macd": float(latest["macd"]),
            "macd_signal": float(latest["macd_signal"]),
            "macd_hist": float(latest["macd_hist"]),
            "bb_pct_b": float(latest["bb_pct_b"]),
            "bb_bandwidth": float(latest["bb_bandwidth"]),
            "atr_14": float(latest["atr_14"]),
            "dist_sma_20": float(latest["dist_sma_20"]),
            "dist_sma_50": float(latest["dist_sma_50"]),
            "ema_9_21_cross": float(latest["ema_9_21_cross"]),
            "vol_ratio": float(latest["vol_ratio"]),
            "return_1d": float(latest["return_1d"]),
            "return_3d": float(latest["return_3d"]),
            "return_5d": float(latest["return_5d"]),
            "body_ratio": float(latest["body_ratio"]),
            "sentiment_score": float(sentiment_score)
        }
        return feature_dict
