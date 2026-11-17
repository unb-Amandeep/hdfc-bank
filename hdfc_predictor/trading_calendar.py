"""
NSE Trading Calendar & Intraday Timestamp Engine.
Handles Indian Standard Time (IST), NSE trading holidays, order expiry calculations,
and strict labeling ("Last traded, 2:00 PM IST" intraday vs "Close" after 3:30 PM).
"""
from datetime import datetime, date, timedelta, time
from typing import Tuple, List, Optional
import pytz

IST = pytz.timezone("Asia/Kolkata")

# Official NSE Trading Holidays (sample comprehensive calendar including 2024, 2025, 2026)
NSE_HOLIDAYS = {
    # 2026
    date(2026, 1, 26),   # Republic Day
    date(2026, 2, 17),   # Mahashivratri
    date(2026, 3, 3),    # Holi
    date(2026, 3, 20),   # Id-ul-Fitr (Ramzan Id)
    date(2026, 4, 3),    # Good Friday
    date(2026, 4, 14),   # Dr. Baba Saheb Ambedkar Jayanti
    date(2026, 5, 1),    # Maharashtra Day
    date(2026, 5, 27),   # Bakri Id
    date(2026, 6, 26),   # Muharram
    date(2026, 8, 15),   # Independence Day
    date(2026, 10, 2),   # Mahatma Gandhi Jayanti
    date(2026, 10, 20),  # Dussehra
    date(2026, 11, 8),   # Diwali Laxmi Pujan
    date(2026, 11, 10),  # Diwali Balipratipada
    date(2026, 11, 24),  # Gurunanak Jayanti
    date(2026, 12, 25),  # Christmas
    # 2025
    date(2025, 1, 26), date(2025, 2, 26), date(2025, 3, 14), date(2025, 3, 31),
    date(2025, 4, 10), date(2025, 4, 14), date(2025, 4, 18), date(2025, 5, 1),
    date(2025, 8, 15), date(2025, 10, 2), date(2025, 10, 21), date(2025, 11, 5),
    date(2025, 12, 25),
}


class TradingCalendar:
    @classmethod
    def get_ist_now(cls) -> datetime:
        return datetime.now(IST)

    @classmethod
    def is_trading_day(cls, d: date) -> bool:
        # Weekend check: Saturday (5), Sunday (6)
        if d.weekday() >= 5:
            return False
        # Holiday check
        if d in NSE_HOLIDAYS:
            return False
        return True

    @classmethod
    def get_price_timing_label(cls, dt: Optional[datetime] = None) -> Tuple[str, bool]:
        """
        Labels the price 'Last traded, 2:00 PM IST (partial bar)' intraday (09:15 to 15:30 IST),
        and 'Close' only after 3:30 PM IST or on non-trading days.
        """
        now = dt if dt is not None else cls.get_ist_now()
        current_date = now.date()
        current_time = now.time()

        is_trading = cls.is_trading_day(current_date)
        market_open = time(9, 15)
        market_close = time(15, 30)

        if is_trading and market_open <= current_time < market_close:
            # Intraday
            time_str = now.strftime("%I:%M %p IST")
            return f"Last traded, {time_str} (partial intraday bar)", True
        else:
            # Closed session
            date_str = current_date.strftime("%Y-%m-%d")
            return f"{date_str} Close", False

    @classmethod
    def calculate_order_expiry(cls, start_dt: Optional[datetime] = None, trading_days: int = 5) -> Tuple[str, str]:
        """
        Calculates order expiry by advancing strictly through NSE trading days,
        skipping weekends and official NSE holidays.
        """
        curr = (start_dt if start_dt is not None else cls.get_ist_now()).date()
        days_counted = 0
        target = curr

        while days_counted < trading_days:
            target += timedelta(days=1)
            if cls.is_trading_day(target):
                days_counted += 1

        formatted_date = target.strftime("%b %d, %Y")
        iso_date = target.strftime("%Y-%m-%d")
        label = f"Limit Order Valid: {trading_days} Trading Days (Expires {formatted_date})"
        return iso_date, label
