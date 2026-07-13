import pandas as pd

from app.strategies.base import Strategy


class MomentumStrategy(Strategy):
    id = "momentum"
    name = "Time-Series Momentum"
    description = "Long when the trailing N-day return is above a threshold, flat otherwise."

    def generate_signals(self, prices: pd.DataFrame, params: dict) -> pd.Series:
        lookback = int(params.get("lookback_days", 90))
        threshold_pct = float(params.get("threshold_pct", 0.0))

        trailing_return = prices["close"].pct_change(periods=lookback)
        signal = (trailing_return > threshold_pct / 100).astype(int)
        signal[trailing_return.isna()] = 0
        return signal
