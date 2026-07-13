"""
Data ingestion for daily OHLCV bars.

Primary source: Yahoo Finance via the `yfinance` package (free, no API key,
~5-10+ years of clean daily equity history for the fixed universe in
universe.py). Results are cached in the `price_bars` Postgres table so a
given ticker/date-range combination is only fetched from Yahoo once.

`yfinance.download` is called with auto_adjust=True (its own default),
meaning Open/High/Low/Close come back already adjusted for splits and
dividends -- that adjusted series is what a backtester should trade on, so
`close` and `adj_close` below are intentionally the same series unless a
distinct "Adj Close" column is present.

USE_SYNTHETIC_DATA=true switches this module to a deterministic synthetic
random-walk generator instead of calling Yahoo Finance at all. That path
exists only so this project can be run and tested with no outbound network
access (e.g. this sandbox). It is OFF by default and must stay off for
anything meant to reflect real market history.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sqlalchemy import and_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import PriceBar

logger = logging.getLogger(__name__)
settings = get_settings()

REQUIRED_COLUMNS = ["open", "high", "low", "close", "adj_close", "volume"]


class DataIngestionError(Exception):
    pass


# ---------------------------------------------------------------------------
# Real source: Yahoo Finance
# ---------------------------------------------------------------------------


def fetch_from_yfinance(ticker: str, start: date, end: date) -> pd.DataFrame:
    import yfinance as yf

    try:
        raw = yf.download(
            ticker,
            start=start,
            # yfinance treats `end` as exclusive; add a day so the caller's
            # end_date is included.
            end=end + timedelta(days=1),
            auto_adjust=True,
            multi_level_index=False,
            threads=False,
            progress=False,
        )
    except Exception as e:  # network errors, parsing errors, etc.
        raise DataIngestionError(f"Yahoo Finance request failed for {ticker}: {e}") from e

    if raw is None or raw.empty:
        raise DataIngestionError(
            f"Yahoo Finance returned no data for '{ticker}' between {start} and {end}. "
            "Check the ticker is correct and that this environment has outbound "
            "network access to query1/query2.finance.yahoo.com."
        )

    raw = raw.rename(
        columns={
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Adj Close": "adj_close",
            "Volume": "volume",
        }
    )
    if "adj_close" not in raw.columns:
        raw["adj_close"] = raw["close"]
    raw.index.name = "date"
    return raw[REQUIRED_COLUMNS].dropna(subset=["open", "high", "low", "close"])


# ---------------------------------------------------------------------------
# Synthetic fallback (offline testing only -- see module docstring)
# ---------------------------------------------------------------------------


def _seed_from_ticker(ticker: str) -> int:
    return int(hashlib.sha256(ticker.encode()).hexdigest(), 16) % (2**32)


def generate_synthetic_ohlcv(ticker: str, start: date, end: date) -> pd.DataFrame:
    """Deterministic, per-ticker synthetic daily OHLCV. NOT real market data."""
    rng = np.random.default_rng(_seed_from_ticker(ticker))
    dates = pd.bdate_range(start=start, end=end)
    n = len(dates)
    if n == 0:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    daily_vol = 0.016
    drift = 0.00025
    shocks = rng.normal(loc=drift, scale=daily_vol, size=n)
    start_price = float(rng.uniform(20, 320))
    closes = start_price * np.exp(np.cumsum(shocks))

    prev_closes = np.concatenate([[start_price], closes[:-1]])
    gaps = rng.normal(0, daily_vol * 0.3, size=n)
    opens = prev_closes * (1 + gaps)
    intraday_range = np.abs(rng.normal(0, daily_vol * 0.6, size=n))
    highs = np.maximum(opens, closes) * (1 + intraday_range)
    lows = np.minimum(opens, closes) * (1 - intraday_range)
    volumes = rng.integers(2_000_000, 25_000_000, size=n)

    df = pd.DataFrame(
        {
            "open": opens,
            "high": highs,
            "low": lows,
            "close": closes,
            "adj_close": closes,
            "volume": volumes,
        },
        index=pd.DatetimeIndex(dates, name="date"),
    )
    return df.round(2)


def fetch_ohlcv(ticker: str, start: date, end: date) -> pd.DataFrame:
    if settings.use_synthetic_data:
        logger.warning("USE_SYNTHETIC_DATA=true: generating synthetic bars for %s (NOT real data).", ticker)
        return generate_synthetic_ohlcv(ticker, start, end)
    return fetch_from_yfinance(ticker, start, end)


# ---------------------------------------------------------------------------
# Postgres cache
# ---------------------------------------------------------------------------


def _query_cached(db: Session, ticker: str, start: date, end: date) -> pd.DataFrame:
    rows = (
        db.query(PriceBar)
        .filter(and_(PriceBar.ticker == ticker, PriceBar.date >= start, PriceBar.date <= end))
        .order_by(PriceBar.date)
        .all()
    )
    if not rows:
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    df = pd.DataFrame(
        [
            {
                "date": r.date,
                "open": r.open,
                "high": r.high,
                "low": r.low,
                "close": r.close,
                "adj_close": r.adj_close,
                "volume": r.volume,
            }
            for r in rows
        ]
    ).set_index("date")
    return df


def _upsert_bars(db: Session, ticker: str, df: pd.DataFrame) -> None:
    if df.empty:
        return
    records = [
        {
            "ticker": ticker,
            "date": idx.date() if hasattr(idx, "date") else idx,
            "open": float(row.open),
            "high": float(row.high),
            "low": float(row.low),
            "close": float(row.close),
            "adj_close": float(row.adj_close),
            "volume": int(row.volume),
        }
        for idx, row in df.iterrows()
    ]
    stmt = pg_insert(PriceBar).values(records)
    stmt = stmt.on_conflict_do_update(
        index_elements=["ticker", "date"],
        set_={
            "open": stmt.excluded.open,
            "high": stmt.excluded.high,
            "low": stmt.excluded.low,
            "close": stmt.excluded.close,
            "adj_close": stmt.excluded.adj_close,
            "volume": stmt.excluded.volume,
        },
    )
    db.execute(stmt)
    db.commit()


def get_price_data(db: Session, ticker: str, start: date, end: date) -> pd.DataFrame:
    """
    Cache-or-fetch daily OHLCV for [start, end] inclusive.

    If the Postgres cache already covers the requested range (within a
    week's tolerance at each edge, to allow for weekends/holidays at the
    boundary) it's returned as-is. Otherwise the full range is fetched
    fresh from the source and upserted -- this project intentionally does
    not attempt to stitch partial ranges, to keep the caching logic simple
    and easy to reason about.
    """
    cached = _query_cached(db, ticker, start, end)
    covers_range = (
        not cached.empty
        and cached.index.min() <= start + timedelta(days=7)
        and cached.index.max() >= end - timedelta(days=7)
    )
    if covers_range:
        return cached

    fresh = fetch_ohlcv(ticker, start, end)
    if fresh.empty:
        return cached
    _upsert_bars(db, ticker, fresh)
    return _query_cached(db, ticker, start, end)
