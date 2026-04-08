from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable

import pandas as pd
import yfinance as yf


class MarketDataProvider(ABC):
    @abstractmethod
    def get_history(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        raise NotImplementedError


class YFinanceDataProvider(MarketDataProvider):
    def __init__(self, cache_dir: str = "cache") -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cache_path(self, symbol: str, start: str, end: str, interval: str) -> Path:
        return self.cache_dir / f"{symbol}_{start}_{end}_{interval}.csv"

    def get_history(self, symbol: str, start: str, end: str, interval: str = "1d") -> pd.DataFrame:
        cache = self._cache_path(symbol, start, end, interval)
        if cache.exists():
            df = pd.read_csv(cache, index_col=0, parse_dates=True)
            return df

        df = yf.download(symbol, start=start, end=end, interval=interval, auto_adjust=False, progress=False)
        if df.empty:
            return df
        df = df.rename(columns=str.title)
        expected = ["Open", "High", "Low", "Close", "Adj Close", "Volume"]
        for col in expected:
            if col not in df.columns:
                df[col] = pd.NA
        df = df[expected]
        df.to_csv(cache)
        return df

    def get_batch(self, symbols: Iterable[str], start: str, end: str, interval: str = "1d") -> dict[str, pd.DataFrame]:
        out = {}
        for s in symbols:
            out[s] = self.get_history(s, start, end, interval)
        return out
