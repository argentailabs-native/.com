from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass
class Position:
    symbol: str
    qty: int
    entry_price: float
    stop_price: float
    target_price: float
    entry_date: pd.Timestamp


@dataclass
class Trade:
    symbol: str
    side: str
    qty: int
    entry_date: pd.Timestamp
    exit_date: pd.Timestamp
    entry_price: float
    exit_price: float
    pnl: float
    pnl_pct: float
    reason: str
    hold_days: int
