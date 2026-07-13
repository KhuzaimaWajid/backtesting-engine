from abc import ABC, abstractmethod

import pandas as pd


class Strategy(ABC):
    """
    A rule-based strategy turns a price history into a target position series.

    Contract for generate_signals:
      - Input `prices` is indexed by date with columns
        open, high, low, close, adj_close, volume.
      - Output is a Series aligned to `prices.index` with values in {0, 1}:
        1 = target long, 0 = target flat. Long/flat only -- no shorting,
        no leverage, no partial sizing at the strategy level.
      - A signal at index t may only depend on prices.loc[:t] (i.e. data
        through that bar's close). The backtest engine, not the strategy,
        is responsible for shifting execution to the next bar so this
        constraint doesn't leak into fills.
    """

    id: str
    name: str
    description: str

    @abstractmethod
    def generate_signals(self, prices: pd.DataFrame, params: dict) -> pd.Series:
        raise NotImplementedError
