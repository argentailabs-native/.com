from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import yfinance as yf


@dataclass
class ScreenResult:
    passed: list[str]
    failed: dict[str, str]


class LiquidityScreener:
    def __init__(self, min_price: float, min_avg_volume: int, min_avg_dollar_volume: float, min_market_cap: float | None = None):
        self.min_price = min_price
        self.min_avg_volume = min_avg_volume
        self.min_avg_dollar_volume = min_avg_dollar_volume
        self.min_market_cap = min_market_cap

    def screen(self, symbols: Iterable[str]) -> ScreenResult:
        passed: list[str] = []
        failed: dict[str, str] = {}

        for symbol in symbols:
            try:
                t = yf.Ticker(symbol)
                hist = t.history(period="3mo", interval="1d")
                if hist.empty:
                    failed[symbol] = "no_history"
                    continue
                avg_close = float(hist["Close"].tail(20).mean())
                avg_vol = float(hist["Volume"].tail(20).mean())
                avg_dollar = avg_close * avg_vol
                if avg_close < self.min_price:
                    failed[symbol] = f"price<{self.min_price}"
                    continue
                if avg_vol < self.min_avg_volume:
                    failed[symbol] = f"volume<{self.min_avg_volume}"
                    continue
                if avg_dollar < self.min_avg_dollar_volume:
                    failed[symbol] = f"dollar_vol<{self.min_avg_dollar_volume}"
                    continue
                if self.min_market_cap is not None:
                    mc = t.fast_info.get("marketCap") if hasattr(t, "fast_info") else None
                    if mc is None or mc < self.min_market_cap:
                        failed[symbol] = f"market_cap<{self.min_market_cap}"
                        continue
                passed.append(symbol)
            except Exception as exc:
                failed[symbol] = f"error:{exc}"
        return ScreenResult(passed=passed, failed=failed)
