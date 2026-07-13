# Backtest Engine

Simulates rule-based trading strategies against historical daily US equity
data: configure a strategy and a ticker, run it, get trades, an equity
curve, and risk/return metrics.

This is scoped deliberately narrow. It is **not** a multi-asset, multi-year,
strategy-DSL platform — see [Assumptions & limitations](#assumptions--limitations)
for exactly what that means.

## Stack

- **Backend**: FastAPI + SQLAlchemy + Postgres, pure-Python backtest engine (pandas/numpy)
- **Data**: `yfinance` (free, no API key), cached in Postgres
- **Frontend**: React + TypeScript (Vite), recharts for the equity curve
- **Storage**: PostgreSQL — every backtest run persists its full config and results

## Quickstart (Docker)

```bash
docker compose up --build
```

This starts Postgres and the backend API on `http://localhost:8000`. Then, in a
second terminal, run the frontend (not dockerized, for a faster dev loop):

```bash
cd frontend
npm install
npm run dev
```

Open the printed local URL (Vite defaults to `http://localhost:5173`).

## Quickstart (manual, no Docker)

```bash
# 1. Postgres — create a database and user matching backend/.env.example,
#    or point DATABASE_URL at any Postgres instance you already have.

# 2. Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit DATABASE_URL if needed
uvicorn app.main:app --reload

# 3. (optional) pre-populate the price cache so first backtests are instant
python -m scripts.seed_data --years 8

# 4. Frontend, in a second terminal
cd frontend
npm install
cp .env.example .env.local   # edit VITE_API_BASE_URL if your backend isn't on :8000
npm run dev
```

## API

| Endpoint | Method | Purpose |
|---|---|---|
| `/strategies` | GET | List the 3 available strategies and their configurable parameters |
| `/tickers` | GET | The fixed 30-ticker universe |
| `/backtest/run` | POST | Run a backtest and persist it |
| `/backtest/results` | GET | List past runs (summary: id, ticker, strategy, headline metrics) |
| `/backtest/results/{id}` | GET | Full detail for one run: config, metrics, equity curve, trades |

Interactive OpenAPI docs are served at `/docs` once the backend is running.

Example request to `/backtest/run`:

```json
{
  "ticker": "AAPL",
  "strategy_id": "ma_crossover",
  "params": { "fast_window": 20, "slow_window": 50 },
  "start_date": "2019-01-01",
  "end_date": "2023-12-31",
  "initial_capital": 100000,
  "commission_bps": 5,
  "slippage_bps": 5,
  "fill_timing": "next_open"
}
```

## Strategies

| Strategy | `strategy_id` | Parameters |
|---|---|---|
| Moving Average Crossover | `ma_crossover` | `fast_window`, `slow_window` |
| RSI Mean Reversion | `rsi_mean_reversion` | `rsi_period`, `oversold_threshold`, `exit_threshold` |
| Time-Series Momentum | `momentum` | `lookback_days`, `threshold_pct` |

All three are long/flat only and return a daily target position in `{0, 1}`; see
`backend/app/strategies/` for the exact rule for each.

## Metrics

Six metrics, computed from the daily equity curve in `backend/app/backtest/metrics.py`:
**Total Return, CAGR, Volatility (annualized), Sharpe Ratio, Max Drawdown, Win Rate**
(win rate is over *closed* round-trip trades only). Each is a standard textbook formula —
see the docstring at the top of that file for the exact math.

## Assumptions & limitations

Explicit, on purpose, so nothing here is claimed to be more than it is:

- **Universe**: a fixed list of 30 large-cap US equities (`backend/app/data/universe.py`),
  not an open ticker search, and not futures/forex (no free, clean source for those).
- **History**: daily bars only, capped at 10 years per backtest request.
- **Fills**: signals are computed using data through a bar's close; by default orders fill
  at the **next bar's open** (no look-ahead). A `same_close` mode is also available — it fills
  at the same bar's close the signal was computed from, a common simplification, not a
  guarantee you could have traded at that exact price in real time.
- **Position**: single position, long/flat only. No shorting, no leverage, no portfolios —
  one ticker per backtest run.
- **Sizing**: on entry, as many whole shares as available cash allows (100% notional). No
  fractional shares.
- **Costs**: commission and slippage are both flat basis-point assumptions applied to trade
  notional, not a real order-book/market-impact model.
- **Idle cash**: earns 0% — no cash interest is modeled.
- **Data**: yfinance is a free, unofficial source. It's generally clean for large-cap US
  equities but isn't SLA-backed; if a fetch fails, the API returns a clear error rather than
  silently substituting anything.
- **No strategy DSL**: three parameterized rule sets, not a scripting language. Adding a new
  strategy means adding a Python class in `backend/app/strategies/`.

## Testing

```bash
cd backend
source .venv/bin/activate
pytest tests/ -v
```

40 tests: metrics formulas, strategy signal logic, engine execution mechanics (fills, costs,
round-trip P&L), and full API integration tests that run against a real Postgres database
(not mocked) using a deterministic synthetic price generator so they don't require network
access to Yahoo Finance. See `backend/app/data/ingestion.py`'s docstring for how that
generator is gated behind `USE_SYNTHETIC_DATA` and why it must stay off in normal use.

## Project structure

```
backend/
  app/
    data/           ticker universe, yfinance ingestion + Postgres cache
    strategies/      base class, the 3 strategies, the param-schema registry
    backtest/        engine.py (fills/cash/position loop), metrics.py, runner.py (orchestration)
    routers/         strategies.py, tickers.py, backtest.py
    models.py        SQLAlchemy: PriceBar, BacktestRun, BacktestTrade
    schemas.py       Pydantic request/response models
    main.py          FastAPI app
  scripts/seed_data.py   CLI to pre-populate the price cache
  tests/
frontend/
  src/
    components/      StrategyForm, MetricsReadout, EquityCurveChart, TradesTable, RunHistory
    api.ts, types.ts
    App.tsx
docker-compose.yml
```

## What's deliberately not built

Multi-asset/portfolio backtests, shorting/leverage, a strategy-scripting DSL, user auth,
Alembic migrations (schema is created via `create_all` on startup — fine for this scope,
not how you'd run this in a real production environment), and a cash-interest model. These
are straightforward extensions on top of this structure, not architectural rewrites, but
they're out of scope here on purpose.
