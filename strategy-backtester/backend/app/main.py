from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import backtest, strategies, tickers

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Backtest Engine API",
    description="Simulates rule-based trading strategies against historical daily equity data.",
    version="0.1.0",
)

# Permissive CORS: this is a local dev / demo tool with no auth or sensitive
# data. Lock this down to a real origin allowlist before deploying anywhere
# public.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(strategies.router, prefix="/strategies", tags=["strategies"])
app.include_router(tickers.router, prefix="/tickers", tags=["tickers"])
app.include_router(backtest.router, prefix="/backtest", tags=["backtest"])


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
