"""
Bar-by-bar backtest execution engine for a single instrument, long/flat only.

Explicit assumptions (all deliberate, all configurable where noted):

  Fills:            signals are decided using data through bar t's close.
                     fill_timing="next_open" (default) executes at bar t+1's
                     OPEN -- no look-ahead. fill_timing="same_close" executes
                     at bar t's own close instead: a common simplification in
                     lightweight backtesters, but note this fills at the same
                     price the signal itself was computed from.
  Sizing:            on entry, buy as many whole shares as available cash
                     allows (100% notional). No fractional shares, no
                     leverage, no shorting. Leftover cash from rounding down
                     to a whole share sits idle.
  Costs:             commission_bps and slippage_bps are both flat, applied
                     to trade notional. Slippage moves the fill price against
                     the trader (buys fill higher, sells fill lower).
  Idle cash:         earns 0% -- no cash interest is modeled.
  Round-trip P&L:    only *closed* buy->sell pairs count toward win rate; a
                     position still open at the end of the window is marked
                     to market in the equity curve but isn't scored as a win
                     or a loss.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date as date_

import numpy as np
import pandas as pd


@dataclass
class Trade:
    date: date_
    side: str  # "BUY" | "SELL"
    shares: int
    price: float
    commission: float
    value: float  # trade notional (shares * price), excluding commission


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame  # indexed by date; columns: equity, cash, position_value, shares
    trades: list[Trade]
    round_trip_pnls: list[float]


def run_backtest(
    prices: pd.DataFrame,
    signals: pd.Series,
    initial_capital: float = 100_000.0,
    commission_bps: float = 5.0,
    slippage_bps: float = 5.0,
    fill_timing: str = "next_open",
) -> BacktestResult:
    if fill_timing not in ("next_open", "same_close"):
        raise ValueError("fill_timing must be 'next_open' or 'same_close'")

    prices = prices.sort_index()
    signals = signals.reindex(prices.index).fillna(0).astype(int)

    if fill_timing == "next_open":
        target_position = signals.shift(1).fillna(0).astype(int)
        fill_prices = prices["open"]
    else:
        target_position = signals
        fill_prices = prices["close"]

    cash = float(initial_capital)
    shares = 0
    position = 0
    trades: list[Trade] = []
    round_trip_pnls: list[float] = []
    open_trade_cost: float | None = None
    equity_rows = []

    for i, dt in enumerate(prices.index):
        fill_price = float(fill_prices.iloc[i])
        desired = int(target_position.iloc[i])

        if desired != position and fill_price > 0 and not np.isnan(fill_price):
            if desired == 1 and position == 0:
                exec_price = fill_price * (1 + slippage_bps / 10_000)
                affordable_shares = int(cash // (exec_price * (1 + commission_bps / 10_000)))
                if affordable_shares > 0:
                    notional = affordable_shares * exec_price
                    commission = notional * commission_bps / 10_000
                    cash -= notional + commission
                    shares += affordable_shares
                    position = 1
                    open_trade_cost = notional + commission
                    trades.append(
                        Trade(_to_date(dt), "BUY", affordable_shares, exec_price, commission, notional)
                    )
            elif desired == 0 and position == 1 and shares > 0:
                exec_price = fill_price * (1 - slippage_bps / 10_000)
                notional = shares * exec_price
                commission = notional * commission_bps / 10_000
                proceeds = notional - commission
                cash += proceeds
                trades.append(Trade(_to_date(dt), "SELL", shares, exec_price, commission, notional))
                if open_trade_cost is not None:
                    round_trip_pnls.append(proceeds - open_trade_cost)
                    open_trade_cost = None
                shares = 0
                position = 0

        mark_price = float(prices["close"].iloc[i])
        position_value = shares * mark_price
        equity_rows.append(
            {
                "date": _to_date(dt),
                "equity": cash + position_value,
                "cash": cash,
                "position_value": position_value,
                "shares": shares,
            }
        )

    equity_df = pd.DataFrame(equity_rows).set_index("date")
    return BacktestResult(equity_curve=equity_df, trades=trades, round_trip_pnls=round_trip_pnls)


def _to_date(dt) -> date_:
    return dt.date() if hasattr(dt, "date") else dt
