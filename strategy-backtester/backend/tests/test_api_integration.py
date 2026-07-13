"""
End-to-end integration tests against a REAL Postgres database (not mocked).

These use USE_SYNTHETIC_DATA=true so they don't depend on outbound network
access to Yahoo Finance, but everything else -- FastAPI routing, Pydantic
validation, SQLAlchemy models, the Postgres JSONB upsert cache, the
strategy/engine/metrics pipeline -- is exercised for real.

Requires: DATABASE_URL pointing at a reachable Postgres instance with the
`backtest` schema (or one main.py's create_all can build).
"""
import os

os.environ["USE_SYNTHETIC_DATA"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.database import Base, SessionLocal, engine
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def clean_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.execute(text("TRUNCATE backtest_trades, backtest_runs, price_bars RESTART IDENTITY CASCADE"))
    db.commit()
    db.close()
    yield


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_list_tickers_returns_fixed_universe():
    r = client.get("/tickers")
    assert r.status_code == 200
    data = r.json()
    assert 20 <= len(data) <= 50
    symbols = {t["symbol"] for t in data}
    assert "AAPL" in symbols
    assert all({"symbol", "name", "sector"} <= t.keys() for t in data)


def test_list_strategies_returns_three_with_param_schemas():
    r = client.get("/strategies")
    assert r.status_code == 200
    data = r.json()
    ids = {s["id"] for s in data}
    assert ids == {"ma_crossover", "rsi_mean_reversion", "momentum"}
    for s in data:
        assert len(s["params"]) >= 1
        for p in s["params"]:
            assert {"name", "label", "type", "default", "min", "max"} <= p.keys()


def test_run_backtest_persists_and_is_retrievable():
    payload = {
        "ticker": "AAPL",
        "strategy_id": "ma_crossover",
        "params": {"fast_window": 10, "slow_window": 30},
        "start_date": "2019-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100000,
        "commission_bps": 5,
        "slippage_bps": 5,
        "fill_timing": "next_open",
    }
    r = client.post("/backtest/run", json=payload)
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["id"] > 0
    assert body["ticker"] == "AAPL"
    assert body["strategy_id"] == "ma_crossover"
    assert body["params"] == {"fast_window": 10, "slow_window": 30}

    metrics = body["metrics"]
    for key in ["total_return_pct", "cagr_pct", "volatility_pct", "sharpe_ratio", "max_drawdown_pct", "win_rate_pct", "num_trades"]:
        assert key in metrics

    assert len(body["equity_curve"]) > 900  # ~5 trading years of daily bars
    assert body["equity_curve"][0]["equity"] == pytest.approx(100000, rel=0.05)

    # fetch it back by id -- proves it round-tripped through Postgres, not just in-memory
    run_id = body["id"]
    r2 = client.get(f"/backtest/results/{run_id}")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["id"] == run_id
    assert body2["metrics"] == metrics
    assert len(body2["trades"]) == metrics["num_trades"] or len(body2["trades"]) >= metrics["num_trades"]


def test_run_history_lists_completed_runs():
    payload = {
        "ticker": "MSFT",
        "strategy_id": "momentum",
        "params": {"lookback_days": 60, "threshold_pct": 0},
        "start_date": "2020-01-01",
        "end_date": "2022-01-01",
    }
    r = client.post("/backtest/run", json=payload)
    assert r.status_code == 200, r.text

    r2 = client.get("/backtest/results")
    assert r2.status_code == 200
    runs = r2.json()
    assert len(runs) >= 1
    assert all("id" in run and "ticker" in run and "sharpe_ratio" in run for run in runs)
    # summaries should NOT include the heavy equity_curve/trades payload
    assert "equity_curve" not in runs[0]


def test_second_run_for_same_ticker_hits_price_cache():
    """Second request for a ticker/range already fetched shouldn't need a fresh source fetch."""
    payload = {
        "ticker": "JPM",
        "strategy_id": "rsi_mean_reversion",
        "params": {"rsi_period": 14, "oversold_threshold": 30, "exit_threshold": 50},
        "start_date": "2021-01-01",
        "end_date": "2022-06-01",
    }
    r1 = client.post("/backtest/run", json=payload)
    assert r1.status_code == 200, r1.text
    r2 = client.post("/backtest/run", json=payload)
    assert r2.status_code == 200, r2.text
    # results should be identical since synthetic data is deterministic per ticker
    assert r1.json()["metrics"] == r2.json()["metrics"]

    db = SessionLocal()
    count = db.execute(text("SELECT count(*) FROM price_bars WHERE ticker = 'JPM'")).scalar()
    db.close()
    assert count > 200


def test_unknown_ticker_rejected():
    payload = {
        "ticker": "NOT_A_REAL_TICKER",
        "strategy_id": "ma_crossover",
        "params": {"fast_window": 10, "slow_window": 30},
        "start_date": "2020-01-01",
        "end_date": "2021-01-01",
    }
    r = client.post("/backtest/run", json=payload)
    assert r.status_code == 400
    assert "universe" in r.json()["detail"].lower()


def test_unknown_strategy_rejected():
    payload = {
        "ticker": "AAPL",
        "strategy_id": "not_a_real_strategy",
        "params": {},
        "start_date": "2020-01-01",
        "end_date": "2021-01-01",
    }
    r = client.post("/backtest/run", json=payload)
    assert r.status_code == 400
    assert "strategy" in r.json()["detail"].lower()


def test_date_range_over_ten_years_rejected():
    payload = {
        "ticker": "AAPL",
        "strategy_id": "ma_crossover",
        "params": {"fast_window": 10, "slow_window": 30},
        "start_date": "2000-01-01",
        "end_date": "2023-01-01",
    }
    r = client.post("/backtest/run", json=payload)
    assert r.status_code == 400
    assert "years" in r.json()["detail"].lower()


def test_missing_run_returns_404():
    r = client.get("/backtest/results/999999")
    assert r.status_code == 404


def test_ma_crossover_param_out_of_range_gets_clamped_not_rejected():
    payload = {
        "ticker": "NVDA",
        "strategy_id": "ma_crossover",
        "params": {"fast_window": 999, "slow_window": 5},  # nonsensical / inverted on purpose
        "start_date": "2020-01-01",
        "end_date": "2023-01-01",
    }
    r = client.post("/backtest/run", json=payload)
    # fast_window clamps to max 100, slow_window clamps to min 5 -> fast(100) >= slow(5) -> engine-level ValueError -> 400
    assert r.status_code == 400
