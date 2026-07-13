"""
Pre-populate the Postgres price cache for the fixed ticker universe.

Run this once after setting up the database so the first backtest a user
runs doesn't have to wait on a live Yahoo Finance fetch:

    python -m scripts.seed_data --years 8
    python -m scripts.seed_data --years 5 --tickers AAPL,MSFT,NVDA
"""
import argparse
import sys
from datetime import date, timedelta

sys.path.insert(0, ".")

from app.data.ingestion import get_price_data
from app.data.universe import UNIVERSE_SYMBOLS
from app.database import Base, SessionLocal, engine


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--years", type=int, default=8, help="How many years of history to fetch (default: 8)")
    parser.add_argument(
        "--tickers", type=str, default=None, help="Comma-separated tickers to fetch; default is the full universe"
    )
    args = parser.parse_args()

    tickers = args.tickers.split(",") if args.tickers else sorted(UNIVERSE_SYMBOLS)
    unknown = set(tickers) - UNIVERSE_SYMBOLS
    if unknown:
        print(f"Unknown tickers (not in the fixed universe): {sorted(unknown)}")
        sys.exit(1)

    end = date.today()
    start = end - timedelta(days=365 * args.years)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    ok, failed = 0, []
    for ticker in tickers:
        try:
            df = get_price_data(db, ticker, start, end)
            print(f"  {ticker}: {len(df)} bars cached ({start} to {end})")
            ok += 1
        except Exception as e:
            print(f"  {ticker}: FAILED - {e}")
            failed.append(ticker)
    db.close()

    print(f"\nDone. {ok}/{len(tickers)} tickers cached.")
    if failed:
        print(f"Failed: {failed}")
        sys.exit(1)


if __name__ == "__main__":
    main()
