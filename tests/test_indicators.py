import pandas as pd

from swing_bot.indicators.ta import sma


def test_sma_basic():
    s = pd.Series([1, 2, 3, 4, 5])
    out = sma(s, 3)
    assert round(out.iloc[-1], 6) == 4.0
