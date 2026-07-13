import pandas as pd

from app.strategies.base import Strategy


def wilder_rsi(close: pd.Series, period: int) -> pd.Series:
    """
    Standard Wilder's RSI: exponential smoothing of average gains/losses with
    alpha=1/period.

    Edge cases: a pure uptrend (avg_loss=0, avg_gain>0) correctly yields 100
    via inf arithmetic (avg_gain/0 = inf -> 100 - 100/(1+inf) = 100), and a
    pure downtrend (avg_gain=0) yields 0. The one case that needs an explicit
    override is a completely flat run with no gains or losses at all
    (avg_gain=0 and avg_loss=0, i.e. 0/0), which is masked to a neutral 50
    rather than left as NaN or miscomputed as 0 -- a flat market is not the
    same thing as an oversold one.
    """
    delta = close.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, min_periods=period, adjust=False).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    no_movement = (avg_gain == 0) & (avg_loss == 0)
    rsi = rsi.mask(no_movement, 50.0)
    return rsi


class RSIMeanReversionStrategy(Strategy):
    id = "rsi_mean_reversion"
    name = "RSI Mean Reversion"
    description = (
        "Buys when RSI drops below the oversold level (buying the dip); exits back to flat "
        "once RSI recovers above the exit level."
    )

    def generate_signals(self, prices: pd.DataFrame, params: dict) -> pd.Series:
        period = int(params.get("rsi_period", 14))
        oversold = float(params.get("oversold_threshold", 30))
        exit_level = float(params.get("exit_threshold", 50))

        rsi = wilder_rsi(prices["close"], period)

        position = pd.Series(0, index=prices.index, dtype=int)
        in_position = False
        for i in range(len(rsi)):
            r = rsi.iloc[i]
            if pd.isna(r):
                position.iloc[i] = 0
                continue
            if not in_position and r < oversold:
                in_position = True
            elif in_position and r > exit_level:
                in_position = False
            position.iloc[i] = 1 if in_position else 0
        return position
