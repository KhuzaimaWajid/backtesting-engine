from datetime import date

import pandas as pd
from sqlalchemy.orm import Session

from app.backtest.engine import run_backtest
from app.backtest.metrics import compute_all_metrics
from app.config import get_settings
from app.data.ingestion import DataIngestionError, get_price_data
from app.strategies.registry import get_strategy, validate_params

settings = get_settings()


class BacktestError(Exception):
    """Raised for any user-facing backtest failure (bad data, bad params, etc.)."""


def execute_backtest(
    db: Session,
    ticker: str,
    strategy_id: str,
    params: dict,
    start_date: date,
    end_date: date,
    initial_capital: float,
    commission_bps: float,
    slippage_bps: float,
    fill_timing: str,
) -> dict:
    try:
        strategy = get_strategy(strategy_id)
    except KeyError as e:
        raise BacktestError(str(e)) from e

    validated_params = validate_params(strategy_id, params)

    try:
        prices = get_price_data(db, ticker, start_date, end_date)
    except DataIngestionError as e:
        raise BacktestError(str(e)) from e

    if prices.empty:
        raise BacktestError(f"No price data available for {ticker} between {start_date} and {end_date}.")

    prices = prices.copy()
    prices.index = pd.to_datetime(prices.index)
    prices = prices.sort_index()
    prices = prices.loc[(prices.index.date >= start_date) & (prices.index.date <= end_date)]

    if len(prices) < settings.min_bars_required:
        raise BacktestError(
            f"Only {len(prices)} trading days of data available for {ticker} in this range; "
            f"need at least {settings.min_bars_required} to run a meaningful backtest. "
            "Try a wider date range."
        )

    try:
        signals = strategy.generate_signals(prices, validated_params)
    except ValueError as e:
        raise BacktestError(str(e)) from e

    result = run_backtest(
        prices=prices,
        signals=signals,
        initial_capital=initial_capital,
        commission_bps=commission_bps,
        slippage_bps=slippage_bps,
        fill_timing=fill_timing,
    )

    metrics = compute_all_metrics(result.equity_curve["equity"], result.round_trip_pnls)

    return {
        "strategy": strategy,
        "validated_params": validated_params,
        "result": result,
        "metrics": metrics,
    }
