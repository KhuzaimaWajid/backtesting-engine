from datetime import date, datetime
from typing import Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field


# ---------- strategies ----------


class StrategyParamSchema(BaseModel):
    name: str
    label: str
    type: Literal["int", "float"]
    default: Union[int, float]
    min: Union[int, float]
    max: Union[int, float]
    step: Union[int, float] = 1


class StrategyInfo(BaseModel):
    id: str
    name: str
    description: str
    params: list[StrategyParamSchema]


# ---------- tickers ----------


class TickerInfo(BaseModel):
    symbol: str
    name: str
    sector: str


# ---------- backtest run: request ----------


class BacktestRunRequest(BaseModel):
    ticker: str
    strategy_id: str
    params: dict[str, float] = Field(default_factory=dict)
    start_date: date
    end_date: date
    initial_capital: float = Field(default=100_000.0, gt=0)
    commission_bps: float = Field(default=5.0, ge=0, le=500)
    slippage_bps: float = Field(default=5.0, ge=0, le=500)
    fill_timing: Literal["next_open", "same_close"] = "next_open"


# ---------- backtest run: response ----------


class TradeSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    date: date
    side: str
    shares: int
    price: float
    commission: float
    value: float


class EquityPoint(BaseModel):
    date: date
    equity: float
    cash: float
    position_value: float
    shares: int


class MetricsSchema(BaseModel):
    total_return_pct: float
    cagr_pct: float
    volatility_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate_pct: float
    num_trades: int


class BacktestRunSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ticker: str
    strategy_id: str
    strategy_name: str
    start_date: date
    end_date: date
    created_at: datetime
    status: str
    total_return_pct: Optional[float] = None
    cagr_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None


class BacktestRunResponse(BaseModel):
    id: int
    ticker: str
    strategy_id: str
    strategy_name: str
    params: dict
    start_date: date
    end_date: date
    initial_capital: float
    commission_bps: float
    slippage_bps: float
    fill_timing: str
    created_at: datetime
    status: str
    error_message: Optional[str] = None
    metrics: MetricsSchema
    equity_curve: list[EquityPoint] = Field(default_factory=list)
    trades: list[TradeSchema] = Field(default_factory=list)
