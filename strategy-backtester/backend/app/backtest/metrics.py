"""
Performance metrics computed from a daily equity curve. Six metrics, each a
standard, textbook formula:

  Total Return   (E_end / E_start) - 1
  CAGR           (E_end / E_start) ** (252 / n_trading_days) - 1
  Volatility     std(daily returns) * sqrt(252)                     [annualized]
  Sharpe Ratio   (mean(daily returns)*252 - rf) / (std(daily returns)*sqrt(252))
  Max Drawdown   min over t of (E_t / running_max(E)_t - 1)
  Win Rate       profitable *closed* round-trip trades / total closed round trips

252 is the standard US-equity trading-day-per-year convention. Risk-free
rate defaults to 0% (configurable) since this project doesn't model a cash
yield on idle balances -- see engine.py's assumptions.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS_PER_YEAR = 252


def compute_returns(equity_curve: pd.Series) -> pd.Series:
    return equity_curve.pct_change().dropna()


def total_return(equity_curve: pd.Series) -> float:
    if len(equity_curve) < 2 or equity_curve.iloc[0] == 0:
        return 0.0
    return float(equity_curve.iloc[-1] / equity_curve.iloc[0] - 1)


def cagr(equity_curve: pd.Series) -> float:
    if len(equity_curve) < 2 or equity_curve.iloc[0] <= 0:
        return 0.0
    n_days = len(equity_curve) - 1
    if n_days <= 0:
        return 0.0
    growth = equity_curve.iloc[-1] / equity_curve.iloc[0]
    if growth <= 0:
        return -1.0
    years = n_days / TRADING_DAYS_PER_YEAR
    return float(growth ** (1 / years) - 1)


def volatility(equity_curve: pd.Series) -> float:
    daily_returns = compute_returns(equity_curve)
    if len(daily_returns) < 2:
        return 0.0
    return float(daily_returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(equity_curve: pd.Series, risk_free_rate: float = 0.0) -> float:
    daily_returns = compute_returns(equity_curve)
    if len(daily_returns) < 2 or daily_returns.std(ddof=1) == 0:
        return 0.0
    excess_annual_return = daily_returns.mean() * TRADING_DAYS_PER_YEAR - risk_free_rate
    annual_vol = daily_returns.std(ddof=1) * np.sqrt(TRADING_DAYS_PER_YEAR)
    return float(excess_annual_return / annual_vol)


def max_drawdown(equity_curve: pd.Series) -> float:
    if equity_curve.empty:
        return 0.0
    running_max = equity_curve.cummax()
    drawdown = equity_curve / running_max - 1
    return float(drawdown.min())


def win_rate(round_trip_pnls: list[float]) -> float:
    if not round_trip_pnls:
        return 0.0
    wins = sum(1 for pnl in round_trip_pnls if pnl > 0)
    return wins / len(round_trip_pnls)


def compute_all_metrics(
    equity_curve: pd.Series, round_trip_pnls: list[float], risk_free_rate: float = 0.0
) -> dict:
    return {
        "total_return_pct": round(total_return(equity_curve) * 100, 4),
        "cagr_pct": round(cagr(equity_curve) * 100, 4),
        "volatility_pct": round(volatility(equity_curve) * 100, 4),
        "sharpe_ratio": round(sharpe_ratio(equity_curve, risk_free_rate), 4),
        "max_drawdown_pct": round(max_drawdown(equity_curve) * 100, 4),
        "win_rate_pct": round(win_rate(round_trip_pnls) * 100, 4),
        "num_trades": len(round_trip_pnls),
    }
