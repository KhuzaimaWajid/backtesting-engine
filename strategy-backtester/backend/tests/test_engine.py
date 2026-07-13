import pandas as pd
import pytest

from app.backtest.engine import run_backtest


def make_prices(opens, closes):
    dates = pd.bdate_range("2020-01-01", periods=len(closes))
    return pd.DataFrame(
        {
            "open": opens,
            "close": closes,
            "high": [max(o, c) for o, c in zip(opens, closes)],
            "low": [min(o, c) for o, c in zip(opens, closes)],
            "adj_close": closes,
            "volume": 1_000_000,
        },
        index=dates,
    )


def test_no_trade_when_signal_always_zero():
    prices = make_prices([100] * 10, [100] * 10)
    signals = pd.Series(0, index=prices.index)
    result = run_backtest(prices, signals, initial_capital=10_000)
    assert len(result.trades) == 0
    assert result.equity_curve["equity"].iloc[-1] == pytest.approx(10_000)


def test_next_open_fill_shifts_execution_by_one_bar():
    n = 10
    closes = [100 + i for i in range(n)]
    opens = closes
    prices = make_prices(opens, closes)
    signals = pd.Series([1] * n, index=prices.index)  # signal is long from the very first bar
    result = run_backtest(
        prices, signals, initial_capital=10_000, commission_bps=0, slippage_bps=0, fill_timing="next_open"
    )
    buys = [t for t in result.trades if t.side == "BUY"]
    sells = [t for t in result.trades if t.side == "SELL"]
    assert len(buys) == 1
    assert len(sells) == 0
    # signal at bar 0's close executes at bar 1's open (101), not bar 0's own price
    assert buys[0].price == pytest.approx(101)
    assert result.equity_curve["equity"].iloc[-1] > 10_000


def test_same_close_fill_executes_on_the_signal_bar_itself():
    n = 5
    closes = [100, 105, 110, 115, 120]
    prices = make_prices(closes, closes)
    signals = pd.Series([1, 1, 1, 1, 1], index=prices.index)
    result = run_backtest(
        prices, signals, initial_capital=10_000, commission_bps=0, slippage_bps=0, fill_timing="same_close"
    )
    assert result.trades[0].price == pytest.approx(100)  # fills at bar 0's own close


def test_round_trip_records_correct_pnl_sign():
    closes = [100, 100, 110, 110, 90, 90]
    prices = make_prices(closes, closes)
    signals = pd.Series([0, 1, 1, 0, 0, 0], index=prices.index)  # buys high (110), sells low (90)
    result = run_backtest(
        prices, signals, initial_capital=10_000, commission_bps=0, slippage_bps=0, fill_timing="next_open"
    )
    assert len(result.trades) == 2
    assert result.trades[0].side == "BUY"
    assert result.trades[1].side == "SELL"
    assert len(result.round_trip_pnls) == 1
    assert result.round_trip_pnls[0] < 0  # bought at 110, sold at 90: a loss


def test_transaction_costs_reduce_equity_versus_zero_cost():
    closes = [100, 100, 110, 110, 90, 90]
    prices = make_prices(closes, closes)
    signals = pd.Series([0, 1, 1, 0, 0, 0], index=prices.index)
    free = run_backtest(prices, signals, initial_capital=10_000, commission_bps=0, slippage_bps=0)
    costly = run_backtest(prices, signals, initial_capital=10_000, commission_bps=50, slippage_bps=50)
    assert costly.equity_curve["equity"].iloc[-1] < free.equity_curve["equity"].iloc[-1]


def test_equity_never_goes_negative_and_cash_plus_position_equals_equity():
    closes = [100, 90, 80, 95, 105, 100]
    prices = make_prices(closes, closes)
    signals = pd.Series([1, 1, 0, 1, 0, 1], index=prices.index)
    result = run_backtest(prices, signals, initial_capital=5_000, commission_bps=10, slippage_bps=10)
    eq = result.equity_curve
    assert (eq["equity"] >= 0).all()
    assert (eq["cash"] + eq["position_value"] - eq["equity"]).abs().max() < 1e-6


def test_invalid_fill_timing_raises():
    prices = make_prices([100] * 5, [100] * 5)
    signals = pd.Series(0, index=prices.index)
    with pytest.raises(ValueError):
        run_backtest(prices, signals, fill_timing="bogus")
