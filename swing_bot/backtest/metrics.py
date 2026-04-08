from __future__ import annotations

import math

import numpy as np
import pandas as pd


def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd = (equity - peak) / peak
    return float(dd.min()) if len(dd) else 0.0


def sharpe(daily_returns: pd.Series, rf: float = 0.0) -> float:
    if daily_returns.std() == 0 or daily_returns.empty:
        return 0.0
    excess = daily_returns - rf / 252
    return float(np.sqrt(252) * excess.mean() / excess.std())


def performance_summary(equity: pd.Series, trades: pd.DataFrame) -> dict:
    ret = equity.pct_change().fillna(0)
    total_return = equity.iloc[-1] / equity.iloc[0] - 1 if len(equity) > 1 else 0
    years = max((equity.index[-1] - equity.index[0]).days / 365.25, 1e-6) if len(equity) > 1 else 1
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1 if len(equity) > 1 else 0

    wins = trades[trades["pnl"] > 0]
    losses = trades[trades["pnl"] <= 0]
    win_rate = len(wins) / len(trades) if len(trades) else 0
    gross_win = wins["pnl"].sum() if len(wins) else 0
    gross_loss = abs(losses["pnl"].sum()) if len(losses) else 0
    profit_factor = gross_win / gross_loss if gross_loss > 0 else math.inf
    avg_win = wins["pnl"].mean() if len(wins) else 0
    avg_loss = losses["pnl"].mean() if len(losses) else 0
    expectancy = trades["pnl"].mean() if len(trades) else 0
    hold = trades["hold_days"].mean() if len(trades) else 0

    return {
        "total_return": float(total_return),
        "cagr": float(cagr),
        "max_drawdown": max_drawdown(equity),
        "win_rate": float(win_rate),
        "profit_factor": float(profit_factor),
        "avg_win": float(avg_win) if pd.notna(avg_win) else 0.0,
        "avg_loss": float(avg_loss) if pd.notna(avg_loss) else 0.0,
        "sharpe": sharpe(ret),
        "expectancy": float(expectancy) if pd.notna(expectancy) else 0.0,
        "num_trades": int(len(trades)),
        "avg_holding_days": float(hold) if pd.notna(hold) else 0.0,
    }
