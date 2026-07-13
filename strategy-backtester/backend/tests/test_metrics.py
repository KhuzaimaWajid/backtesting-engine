import pandas as pd
import pytest

from app.backtest.metrics import (
    cagr,
    compute_all_metrics,
    max_drawdown,
    sharpe_ratio,
    total_return,
    volatility,
    win_rate,
)


def make_equity_curve(values):
    dates = pd.bdate_range("2020-01-01", periods=len(values))
    return pd.Series(values, index=dates, dtype=float)


def test_total_return_simple_growth():
    eq = make_equity_curve([100, 110, 121])
    assert total_return(eq) == pytest.approx(0.21, abs=1e-9)


def test_total_return_flat():
    eq = make_equity_curve([100, 100, 100])
    assert total_return(eq) == pytest.approx(0.0)


def test_max_drawdown_detects_peak_to_trough():
    eq = make_equity_curve([100, 120, 90, 95, 130])  # peak 120 -> trough 90 = -25%
    assert max_drawdown(eq) == pytest.approx(-0.25, abs=1e-9)


def test_max_drawdown_monotonic_up_is_zero():
    eq = make_equity_curve([100, 105, 110, 120])
    assert max_drawdown(eq) == pytest.approx(0.0)


def test_max_drawdown_recovers_and_dips_again_keeps_worst():
    eq = make_equity_curve([100, 50, 100, 40, 100])  # worst is 40/100-1 = -60%
    assert max_drawdown(eq) == pytest.approx(-0.6, abs=1e-9)


def test_volatility_zero_for_constant_returns():
    eq = make_equity_curve([100] * 30)
    assert volatility(eq) == pytest.approx(0.0)


def test_volatility_positive_for_noisy_series():
    eq = make_equity_curve([100, 105, 98, 110, 95, 115, 90])
    assert volatility(eq) > 0


def test_sharpe_positive_for_steady_uptrend():
    values = [100 * (1.001**i) for i in range(60)]
    eq = make_equity_curve(values)
    assert sharpe_ratio(eq) > 0


def test_sharpe_negative_for_steady_downtrend():
    values = [100 * (0.999**i) for i in range(60)]
    eq = make_equity_curve(values)
    assert sharpe_ratio(eq) < 0


def test_sharpe_zero_when_flat():
    eq = make_equity_curve([100] * 30)
    assert sharpe_ratio(eq) == pytest.approx(0.0)


def test_cagr_two_year_double_matches_closed_form():
    n_days = 252 * 2 + 1
    dates = pd.bdate_range("2020-01-01", periods=n_days)
    eq = pd.Series([100 * (2 ** (i / (n_days - 1))) for i in range(n_days)], index=dates)
    result = cagr(eq)
    expected = 2 ** (252 / (n_days - 1)) - 1
    assert result == pytest.approx(expected, rel=1e-6)


def test_win_rate_basic():
    assert win_rate([10, -5, 20, -1]) == pytest.approx(0.5)


def test_win_rate_no_trades():
    assert win_rate([]) == 0.0


def test_win_rate_all_wins():
    assert win_rate([1, 2, 3]) == pytest.approx(1.0)


def test_compute_all_metrics_keys_and_num_trades():
    eq = make_equity_curve([100, 102, 101, 105])
    metrics = compute_all_metrics(eq, [5.0, -2.0])
    expected_keys = {
        "total_return_pct",
        "cagr_pct",
        "volatility_pct",
        "sharpe_ratio",
        "max_drawdown_pct",
        "win_rate_pct",
        "num_trades",
    }
    assert set(metrics.keys()) == expected_keys
    assert metrics["num_trades"] == 2
    assert metrics["win_rate_pct"] == pytest.approx(50.0)
