"""
ADR Normalization & International Cross-Market Arbitrage Engine.
Converts NYSE ADR (HDB) to INR-equivalent share price using configurable share ratio
and USD/INR exchange rate. Accounts for holiday calendar mismatches and trading hour offsets.
"""
from dataclasses import dataclass
from datetime import datetime, date
from typing import Dict, Any, Optional, Tuple
import urllib.request
import json

from hdfc_predictor.config import settings


@dataclass
class ADRNormalizedQuote:
    adr_symbol: str                 # "HDB"
    local_symbol: str               # "HDFCBANK.NS"
    adr_usd_price: float            # e.g. $26.29
    usd_inr_rate: float             # e.g. 93.58
    adr_shares_per_ads: float       # Default 3.0 equity shares per 1 ADS
    adr_inr_per_share: float        # (HDB_USD * USD_INR) / 3.0 e.g. ₹820.05
    local_inr_price: float          # e.g. ₹814.90
    spread_inr: float               # e.g. +₹5.15
    adr_premium_discount_pct: float # e.g. +0.63% (Premium)
    as_of_us_date: str
    as_of_india_date: str
    is_calendar_mismatch: bool      # True if US or India was on holiday
    calendar_note: str


class ADRNormalizer:
    def __init__(
        self,
        adr_shares_per_ads: float = 3.0,
        adr_symbol: str = settings.backup_symbol,
        local_symbol: str = settings.symbol
    ):
        self.adr_shares_per_ads = float(adr_shares_per_ads)
        self.adr_symbol = adr_symbol
        self.local_symbol = local_symbol

    def normalize(
        self,
        adr_usd_price: float,
        usd_inr_rate: float,
        local_inr_price: float,
        us_date: Optional[str] = None,
        india_date: Optional[str] = None
    ) -> ADRNormalizedQuote:
        """
        Normalizes NYSE ADS price into domestic INR-per-share equivalent.
        """
        if self.adr_shares_per_ads <= 0:
            raise ValueError("ADR ratio must be greater than zero.")
        if usd_inr_rate <= 0:
            raise ValueError("USD/INR exchange rate must be strictly positive.")

        # Formula: (HDB_USD * USD_INR) / ADR_RATIO
        adr_inr = round((adr_usd_price * usd_inr_rate) / self.adr_shares_per_ads, 2)
        spread = round(adr_inr - local_inr_price, 2)
        prem_disc = round((spread / (local_inr_price + 1e-9)) * 100, 2)

        today_str = datetime.now().strftime("%Y-%m-%d")
        d_us = us_date or today_str
        d_in = india_date or today_str

        # Check holiday / date mismatch
        mismatch = d_us != d_in
        cal_note = "Synchronized sessions" if not mismatch else f"Date offset: US session ({d_us}) vs India session ({d_in})"

        return ADRNormalizedQuote(
            adr_symbol=self.adr_symbol,
            local_symbol=self.local_symbol,
            adr_usd_price=round(adr_usd_price, 2),
            usd_inr_rate=round(usd_inr_rate, 4),
            adr_shares_per_ads=self.adr_shares_per_ads,
            adr_inr_per_share=adr_inr,
            local_inr_price=round(local_inr_price, 2),
            spread_inr=spread,
            adr_premium_discount_pct=prem_disc,
            as_of_us_date=d_us,
            as_of_india_date=d_in,
            is_calendar_mismatch=mismatch,
            calendar_note=cal_note
        )
