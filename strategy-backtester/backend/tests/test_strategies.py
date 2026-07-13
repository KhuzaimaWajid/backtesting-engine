import numpy as np
import pandas as pd
import pytest

from app.strategies.ma_crossover import MovingAverageCrossoverStrategy
from app.strategies.momentum import MomentumStrategy
from app.strategies.rsi_mean_reversion import RSIMeanReversionStrategy


def make_prices(closes):
    dates = pd.bdate_range("2020-01-01", periods=len(closes))
    df = pd.DataFrame({"close": closes}, index=dates)
    df["open"] = df["close"]
    df["high"] = df["close"]
    df["low"] = df["close"]
    df["adj_close"] = df["close"]
    df["volume"] = 1_000_000
    return df


def test_ma_crossover_goes_long_after_a_rally():
    closes = [100] * 10 + list(np.linspace(100, 160, 20))
    prices = make_prices(closes)
    strat = MovingAverageCrossoverStrategy()
    signal = strat.generate_signals(prices, {"fast_window": 3, "slow_window": 8})
    assert signal.iloc[-1] == 1
    assert signal.iloc[5] == 0  # not enough history yet / still flat


def test_ma_crossover_flat_when_price_never_moves():
    prices = make_prices([100] * 30)
    strat = MovingAverageCrossoverStrategy()
    signal = strat.generate_signals(prices, {"fast_window": 5, "slow_window": 15})
    assert signal.sum() == 0


def test_ma_crossover_rejects_fast_ge_slow():
    prices = make_prices([100] * 20)
    strat = MovingAverageCrossoverStrategy()
    with pytest.raises(ValueError):
        strat.generate_signals(prices, {"fast_window": 10, "slow_window": 10})


def test_rsi_mean_reversion_enters_on_selloff_and_exits_on_recovery():
    closes = [100] * 15 + list(np.linspace(100, 70, 10)) + list(np.linspace(70, 110, 15))
    prices = make_prices(closes)
    strat = RSIMeanReversionStrategy()
    signal = strat.generate_signals(prices, {"rsi_period": 14, "oversold_threshold": 30, "exit_threshold": 50})
    assert signal.max() == 1  # entered long at some point during/after the selloff
    assert signal.iloc[-1] == 0  # and exited again once RSI recovered past the exit level


def test_rsi_stays_flat_on_dead_flat_prices():
    prices = make_prices([100] * 30)
    strat = RSIMeanReversionStrategy()
    signal = strat.generate_signals(prices, {"rsi_period": 14, "oversold_threshold": 30, "exit_threshold": 50})
    assert signal.sum() == 0


def test_momentum_goes_long_on_positive_trailing_return():
    closes = list(np.linspace(100, 150, 40))
    prices = make_prices(closes)
    strat = MomentumStrategy()
    signal = strat.generate_signals(prices, {"lookback_days": 20, "threshold_pct": 0})
    assert signal.iloc[-1] == 1


def test_momentum_flat_on_declining_price():
    closes = list(np.linspace(150, 100, 40))
    prices = make_prices(closes)
    strat = MomentumStrategy()
    signal = strat.generate_signals(prices, {"lookback_days": 20, "threshold_pct": 0})
    assert signal.iloc[-1] == 0
