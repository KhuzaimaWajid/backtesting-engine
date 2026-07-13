from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload

from app.backtest.runner import BacktestError, execute_backtest
from app.config import get_settings
from app.data.universe import UNIVERSE_SYMBOLS
from app.database import get_db
from app.models import BacktestRun, BacktestTrade
from app.schemas import BacktestRunRequest, BacktestRunResponse, BacktestRunSummary
from app.strategies.registry import STRATEGIES

router = APIRouter()
settings = get_settings()


@router.post("/run", response_model=BacktestRunResponse)
def run_backtest_endpoint(req: BacktestRunRequest, db: Session = Depends(get_db)):
    if req.ticker not in UNIVERSE_SYMBOLS:
        raise HTTPException(400, f"Ticker '{req.ticker}' is not in the supported universe. See GET /tickers.")
    if req.strategy_id not in STRATEGIES:
        raise HTTPException(400, f"Unknown strategy_id '{req.strategy_id}'. See GET /strategies.")
    if req.end_date <= req.start_date:
        raise HTTPException(400, "end_date must be after start_date.")
    if (req.end_date - req.start_date).days > settings.max_date_range_years * 365:
        raise HTTPException(
            400,
            f"Date range exceeds {settings.max_date_range_years} years. This project intentionally "
            f"scopes to {settings.max_date_range_years} years of daily equity data, not decades of history.",
        )

    try:
        outcome = execute_backtest(
            db=db,
            ticker=req.ticker,
            strategy_id=req.strategy_id,
            params=req.params,
            start_date=req.start_date,
            end_date=req.end_date,
            initial_capital=req.initial_capital,
            commission_bps=req.commission_bps,
            slippage_bps=req.slippage_bps,
            fill_timing=req.fill_timing,
        )
    except BacktestError as e:
        raise HTTPException(400, str(e))

    strategy = outcome["strategy"]
    result = outcome["result"]
    metrics = outcome["metrics"]

    run = BacktestRun(
        ticker=req.ticker,
        strategy_id=strategy.id,
        strategy_name=strategy.name,
        params=outcome["validated_params"],
        start_date=req.start_date,
        end_date=req.end_date,
        initial_capital=req.initial_capital,
        commission_bps=req.commission_bps,
        slippage_bps=req.slippage_bps,
        fill_timing=req.fill_timing,
        status="completed",
        equity_curve=[
            {
                "date": idx.isoformat(),
                "equity": round(row.equity, 2),
                "cash": round(row.cash, 2),
                "position_value": round(row.position_value, 2),
                "shares": int(row.shares),
            }
            for idx, row in result.equity_curve.iterrows()
        ],
        **metrics,
    )
    run.trades = [
        BacktestTrade(
            date=t.date,
            side=t.side,
            shares=t.shares,
            price=t.price,
            commission=t.commission,
            value=t.value,
        )
        for t in result.trades
    ]

    db.add(run)
    db.commit()
    db.refresh(run)

    return _to_response(run)


@router.get("/results", response_model=list[BacktestRunSummary])
def list_backtest_results(limit: int = 50, db: Session = Depends(get_db)):
    return (
        db.query(BacktestRun)
        .order_by(BacktestRun.created_at.desc())
        .limit(min(limit, 200))
        .all()
    )


@router.get("/results/{run_id}", response_model=BacktestRunResponse)
def get_backtest_result(run_id: int, db: Session = Depends(get_db)):
    run = (
        db.query(BacktestRun)
        .options(joinedload(BacktestRun.trades))
        .filter(BacktestRun.id == run_id)
        .first()
    )
    if run is None:
        raise HTTPException(404, f"Backtest run {run_id} not found.")
    return _to_response(run)


def _to_response(run: BacktestRun) -> BacktestRunResponse:
    return BacktestRunResponse(
        id=run.id,
        ticker=run.ticker,
        strategy_id=run.strategy_id,
        strategy_name=run.strategy_name,
        params=run.params,
        start_date=run.start_date,
        end_date=run.end_date,
        initial_capital=run.initial_capital,
        commission_bps=run.commission_bps,
        slippage_bps=run.slippage_bps,
        fill_timing=run.fill_timing,
        created_at=run.created_at,
        status=run.status,
        error_message=run.error_message,
        metrics={
            "total_return_pct": run.total_return_pct,
            "cagr_pct": run.cagr_pct,
            "volatility_pct": run.volatility_pct,
            "sharpe_ratio": run.sharpe_ratio,
            "max_drawdown_pct": run.max_drawdown_pct,
            "win_rate_pct": run.win_rate_pct,
            "num_trades": run.num_trades,
        },
        equity_curve=run.equity_curve or [],
        trades=[
            {
                "date": t.date,
                "side": t.side,
                "shares": t.shares,
                "price": t.price,
                "commission": t.commission,
                "value": t.value,
            }
            for t in run.trades
        ],
    )
