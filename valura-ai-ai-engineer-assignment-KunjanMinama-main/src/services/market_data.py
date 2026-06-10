"""
Market data service — fetches real-time and historical prices.

Uses yfinance as the primary data source. Falls back to mock data
for tickers that fail (network issues, invalid tickers, etc.).

Design decision: yfinance is free, requires no API key, and covers
all exchanges referenced in the fixtures (NASDAQ, NYSE, EURONEXT,
LSE, TSE). It's the path of least resistance for this assignment.
"""

from __future__ import annotations

import datetime
from typing import Optional

from src.core.logger import get_logger

logger = get_logger(__name__)

# Lazy import yfinance — it may not be installed in all environments
_yf = None


def _get_yf():
    global _yf
    if _yf is None:
        try:
            import yfinance as yf
            _yf = yf
        except ImportError:
            logger.warning("yfinance not installed — using mock market data")
            _yf = False
    return _yf


def get_current_price(ticker: str) -> Optional[float]:
    """
    Get the current/latest price for a ticker.

    Returns None if the ticker cannot be resolved.
    """
    yf = _get_yf()
    if not yf:
        return _mock_price(ticker)

    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        # Try multiple price fields
        for field in ("currentPrice", "regularMarketPrice", "previousClose"):
            price = info.get(field)
            if price is not None and price > 0:
                return float(price)

        # Fallback: use last close from history
        hist = stock.history(period="5d")
        if not hist.empty:
            return float(hist["Close"].iloc[-1])

        return None
    except Exception as e:
        logger.warning(f"Failed to fetch price for {ticker}: {e}")
        return _mock_price(ticker)


def get_historical_prices(
    ticker: str,
    period: str = "1y",
) -> list[dict]:
    """
    Get historical daily close prices for a ticker.

    Returns list of {"date": "YYYY-MM-DD", "close": float}.
    """
    yf = _get_yf()
    if not yf:
        return _mock_historical(ticker, period)

    try:
        stock = yf.Ticker(ticker)
        hist = stock.history(period=period)
        if hist.empty:
            return _mock_historical(ticker, period)

        result = []
        for date, row in hist.iterrows():
            result.append({
                "date": date.strftime("%Y-%m-%d"),
                "close": round(float(row["Close"]), 2),
            })
        return result
    except Exception as e:
        logger.warning(f"Failed to fetch history for {ticker}: {e}")
        return _mock_historical(ticker, period)


def get_benchmark_return(benchmark: str, period: str = "1y") -> Optional[float]:
    """
    Get the total return of a benchmark index over a period.

    Supported benchmarks and their ticker mappings:
      S&P 500     → ^GSPC
      QQQ         → QQQ
      FTSE 100    → ^FTSE
      NIKKEI 225  → ^N225
      MSCI World  → URTH (ETF proxy)
    """
    ticker_map = {
        "S&P 500": "^GSPC",
        "QQQ": "QQQ",
        "FTSE 100": "^FTSE",
        "NIKKEI 225": "^N225",
        "MSCI World": "URTH",
    }

    ticker = ticker_map.get(benchmark, benchmark)
    prices = get_historical_prices(ticker, period)

    if len(prices) < 2:
        return None

    start_price = prices[0]["close"]
    end_price = prices[-1]["close"]

    if start_price <= 0:
        return None

    return round(((end_price - start_price) / start_price) * 100, 2)


# ────────────────────────────────────────────────────────────
# Mock data — used when yfinance is unavailable or fails
# ────────────────────────────────────────────────────────────

_MOCK_PRICES: dict[str, float] = {
    "AAPL": 195.50, "MSFT": 420.80, "NVDA": 880.50, "GOOGL": 175.20,
    "META": 500.10, "AMZN": 185.60, "TSLA": 175.40, "AMD": 165.30,
    "QQQ": 480.50, "VTI": 265.80, "VXUS": 58.90, "BND": 72.10,
    "VOO": 490.20, "ASML.AS": 920.40, "HSBA.L": 7.15, "7203.T": 2800.0,
    "JNJ": 155.80, "PG": 168.40, "KO": 62.50, "VYM": 118.90,
    "SCHD": 82.40, "TLT": 92.30,
    "^GSPC": 5250.0, "^FTSE": 8200.0, "^N225": 38500.0, "URTH": 132.0,
}


def _mock_price(ticker: str) -> Optional[float]:
    """Return a mock price for known tickers."""
    return _MOCK_PRICES.get(ticker.upper())


def _mock_historical(ticker: str, period: str) -> list[dict]:
    """Generate simple mock historical data."""
    current = _mock_price(ticker)
    if current is None:
        return []

    # Generate 252 trading days (1 year) of synthetic data
    days = 252
    if period == "6mo":
        days = 126
    elif period == "3mo":
        days = 63
    elif period == "5d":
        days = 5

    import random
    random.seed(hash(ticker))  # deterministic per ticker

    prices = []
    price = current * 0.85  # start ~15% lower (mock growth)
    today = datetime.date.today()

    for i in range(days):
        date = today - datetime.timedelta(days=days - i)
        # Small random daily return
        daily_return = 1 + random.uniform(-0.02, 0.025)
        price *= daily_return
        prices.append({
            "date": date.strftime("%Y-%m-%d"),
            "close": round(price, 2),
        })

    return prices
