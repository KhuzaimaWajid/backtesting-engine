from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Postgres connection string. Overridden by DATABASE_URL in real deployments
    # (see docker-compose.yml, which points this at the `postgres` service).
    database_url: str = "postgresql://backtest:backtest@localhost:5432/backtest"

    # When true, price data is generated deterministically in-process instead
    # of being pulled from Yahoo Finance. This exists ONLY so the system can
    # be run and tested with no outbound network access. It must never be
    # enabled for anything that claims to reflect real market history.
    use_synthetic_data: bool = False

    # Core-scope guardrail: this project is intentionally limited to
    # 5-10 years of daily equity data, not decades of multi-asset history.
    max_date_range_years: int = 10
    min_bars_required: int = 60

    default_initial_capital: float = 100_000.0
    default_commission_bps: float = 5.0
    default_slippage_bps: float = 5.0


@lru_cache
def get_settings() -> Settings:
    return Settings()
