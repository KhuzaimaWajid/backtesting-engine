from datetime import UTC, datetime

from sqlalchemy import BigInteger, Column, Date, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.database import Base


class PriceBar(Base):
    """Cached daily OHLCV bar. Primary key (ticker, date) so re-fetching is idempotent."""

    __tablename__ = "price_bars"

    ticker = Column(String, primary_key=True)
    date = Column(Date, primary_key=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    adj_close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)


class BacktestRun(Base):
    """A single backtest execution: the config that was used, plus its results."""

    __tablename__ = "backtest_runs"

    id = Column(Integer, primary_key=True, index=True)

    # --- config (what was asked for) ---
    ticker = Column(String, nullable=False, index=True)
    strategy_id = Column(String, nullable=False)
    strategy_name = Column(String, nullable=False)
    params = Column(JSONB, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    initial_capital = Column(Float, nullable=False)
    commission_bps = Column(Float, nullable=False)
    slippage_bps = Column(Float, nullable=False)
    fill_timing = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    status = Column(String, nullable=False, default="completed")
    error_message = Column(String, nullable=True)

    # --- results: the 6 core metrics ---
    total_return_pct = Column(Float, nullable=True)
    cagr_pct = Column(Float, nullable=True)
    volatility_pct = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    max_drawdown_pct = Column(Float, nullable=True)
    win_rate_pct = Column(Float, nullable=True)
    num_trades = Column(Integer, nullable=True)

    # daily equity curve, stored as [{date, equity, cash, position_value, shares}, ...]
    equity_curve = Column(JSONB, nullable=True)

    trades = relationship(
        "BacktestTrade",
        back_populates="run",
        cascade="all, delete-orphan",
        order_by="BacktestTrade.date",
    )


class BacktestTrade(Base):
    """One executed fill (BUY or SELL) belonging to a backtest run."""

    __tablename__ = "backtest_trades"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("backtest_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    side = Column(String, nullable=False)  # "BUY" | "SELL"
    shares = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, nullable=False)
    value = Column(Float, nullable=False)

    run = relationship("BacktestRun", back_populates="trades")
