from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from swing_bot.config.settings import IndicatorConfig, RiskConfig
from swing_bot.indicators.ta import atr, macd, rsi, sma


@dataclass
class Signal:
    symbol: str
    action: str
    entry: float
    stop: float
    target: float
    reason: str


class SwingTrendStrategy:
    def __init__(self, icfg: IndicatorConfig, rcfg: RiskConfig):
        self.icfg = icfg
        self.rcfg = rcfg

    def prepare(self, df: pd.DataFrame) -> pd.DataFrame:
        out = df.copy()
        out["sma_fast"] = sma(out["Close"], self.icfg.sma_fast)
        out["sma_slow"] = sma(out["Close"], self.icfg.sma_slow)
        out["rsi"] = rsi(out["Close"], self.icfg.rsi_period)
        m, s, h = macd(out["Close"], self.icfg.macd_fast, self.icfg.macd_slow, self.icfg.macd_signal)
        out["macd"] = m
        out["macd_signal"] = s
        out["macd_hist"] = h
        out["atr"] = atr(out, self.icfg.atr_period)
        out["avg_vol"] = out["Volume"].rolling(self.icfg.volume_lookback).mean()
        out["recent_high_20"] = out["High"].rolling(20).max()
        out["recent_low_20"] = out["Low"].rolling(20).min()
        return out

    def is_market_regime_bullish(self, regime_df: pd.DataFrame) -> bool:
        if regime_df.empty:
            return True
        r = self.prepare(regime_df).iloc[-1]
        return bool(r["Close"] > r["sma_fast"] and r["sma_fast"] > r["sma_slow"])

    def entry_signal(self, symbol: str, df: pd.DataFrame) -> Signal | None:
        d = self.prepare(df)
        row = d.iloc[-1]
        prev = d.iloc[-2]

        price = float(row["Close"])
        if pd.isna(row["atr"]) or row["atr"] <= 0:
            return None

        trend = price > row["sma_fast"] > row["sma_slow"]
        rsi_ok = self.icfg.rsi_min <= row["rsi"] <= self.icfg.rsi_max
        macd_ok = row["macd"] > row["macd_signal"] and row["macd_hist"] > prev["macd_hist"]
        breakout = price > prev["recent_high_20"] * 0.995
        pullback_continue = (row["Low"] <= row["sma_fast"] * 1.01) and (price >= row["sma_fast"])
        vol_ok = row["Volume"] >= row["avg_vol"]
        not_extended = (price - row["sma_fast"]) / price <= 0.08

        if trend and rsi_ok and macd_ok and (breakout or pullback_continue) and vol_ok and not_extended:
            stop = price - self.rcfg.atr_stop_mult * float(row["atr"])
            risk = price - stop
            target = price + self.rcfg.rr_target * risk
            reason = "trend+rsi+macd+setup+volume"
            return Signal(symbol, "buy", price, stop, target, reason)
        return None

    def exit_signal(self, df: pd.DataFrame, stop: float, entry_date: pd.Timestamp) -> tuple[bool, str, float]:
        d = self.prepare(df)
        row = d.iloc[-1]
        price = float(row["Close"])
        atr_val = float(row["atr"]) if pd.notna(row["atr"]) else 0
        trailing = max(stop, price - self.rcfg.trailing_atr_mult * atr_val) if atr_val > 0 else stop

        if price <= stop:
            return True, "hard_stop", price
        if price < row["sma_fast"] and row["macd"] < row["macd_signal"]:
            return True, "trend_break", price
        if (d.index[-1] - entry_date).days >= self.rcfg.max_holding_days:
            return True, "time_exit", price
        return False, "hold", trailing
