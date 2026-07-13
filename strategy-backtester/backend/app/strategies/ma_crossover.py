import pandas as pd

from app.strategies.base import Strategy


class MovingAverageCrossoverStrategy(Strategy):
    id = "ma_crossover"
    name = "Moving Average Crossover"
    description = "Long while the fast moving average is above the slow moving average, flat otherwise."

    def generate_signals(self, prices: pd.DataFrame, params: dict) -> pd.Series:
        fast_window = int(params.get("fast_window", 20))
        slow_window = int(params.get("slow_window", 50))
        if fast_window >= slow_window:
            raise ValueError("fast_window must be smaller than slow_window")

        fast_ma = prices["close"].rolling(window=fast_window, min_periods=fast_window).mean()
        slow_ma = prices["close"].rolling(window=slow_window, min_periods=slow_window).mean()

        signal = (fast_ma > slow_ma).astype(int)
        signal[fast_ma.isna() | slow_ma.isna()] = 0
        return signal
