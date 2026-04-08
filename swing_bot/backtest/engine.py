from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from swing_bot.backtest.metrics import performance_summary
from swing_bot.config.settings import Settings
from swing_bot.data.data_provider import YFinanceDataProvider
from swing_bot.portfolio.models import Position
from swing_bot.portfolio.portfolio import Portfolio
from swing_bot.risk.risk_manager import RiskManager
from swing_bot.strategy.swing_strategy import SwingTrendStrategy


class BacktestEngine:
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.log = logger
        self.data = YFinanceDataProvider(cache_dir="cache")
        self.strategy = SwingTrendStrategy(settings.indicators, settings.risk)
        self.risk = RiskManager(
            risk_per_trade=settings.risk.risk_per_trade,
            max_positions=settings.risk.max_concurrent_positions,
            max_portfolio_heat=settings.risk.max_portfolio_heat,
            max_daily_loss=settings.risk.max_daily_loss,
            max_weekly_loss=settings.risk.max_weekly_loss,
            max_volatility_ratio=settings.risk.max_volatility_ratio,
        )

    def run(self, symbols: list[str]) -> dict:
        bt = self.settings.backtest
        market = {s: self.data.get_history(s, bt.start_date, bt.end_date) for s in symbols}
        regime = self.data.get_history(self.settings.runtime.regime_filter_symbol, bt.start_date, bt.end_date)

        calendar = sorted(set().union(*[df.index for df in market.values() if not df.empty]))
        p = Portfolio(cash=bt.initial_capital, equity=bt.initial_capital)
        trades = []
        curve = []

        for date in calendar:
            # mark to market
            mtm = p.cash
            for sym, pos in list(p.positions.items()):
                df = market[sym]
                if date not in df.index:
                    continue
                px = float(df.loc[date, "Close"])
                mtm += pos.qty * px
            p.equity = mtm
            curve.append((date, p.equity))

            day_idx = len(curve) - 1
            daily_ret = 0 if day_idx == 0 else (curve[-1][1] / curve[-2][1] - 1)
            week_start = max(0, day_idx - 5)
            weekly_ret = 0 if week_start == day_idx else (curve[-1][1] / curve[week_start][1] - 1)

            # exits first
            for sym, pos in list(p.positions.items()):
                df = market[sym]
                df_now = df[df.index <= date]
                if len(df_now) < 220:
                    continue
                do_exit, reason, stop_or_price = self.strategy.exit_signal(df_now, pos.stop_price, pos.entry_date)
                if do_exit:
                    exit_px = self._apply_costs(stop_or_price, is_buy=False)
                    proceeds = pos.qty * exit_px
                    fee = max(bt.min_commission, bt.commission_per_share * pos.qty)
                    p.cash += proceeds - fee
                    pnl = (exit_px - pos.entry_price) * pos.qty - fee
                    hold = (date - pos.entry_date).days
                    trades.append({
                        "symbol": sym,
                        "side": "long",
                        "qty": pos.qty,
                        "entry_date": pos.entry_date,
                        "exit_date": date,
                        "entry_price": pos.entry_price,
                        "exit_price": exit_px,
                        "pnl": pnl,
                        "pnl_pct": pnl / (pos.entry_price * pos.qty),
                        "reason": reason,
                        "hold_days": hold,
                    })
                    self.log.info("EXIT %s %s qty=%s reason=%s pnl=%.2f", date.date(), sym, pos.qty, reason, pnl)
                    del p.positions[sym]
                else:
                    pos.stop_price = stop_or_price

            # entries
            regime_now = regime[regime.index <= date]
            regime_ok = self.strategy.is_market_regime_bullish(regime_now)
            if not regime_ok:
                continue

            for sym in symbols:
                if sym in p.positions:
                    continue
                df = market[sym]
                df_now = df[df.index <= date]
                if len(df_now) < 220:
                    continue
                signal = self.strategy.entry_signal(sym, df_now)
                if signal is None:
                    continue

                atr_ratio = (signal.entry - signal.stop) / signal.entry
                decision = self.risk.can_open(
                    open_positions=len(p.positions),
                    open_risk=p.open_risk_fraction(),
                    daily_pnl_pct=daily_ret,
                    weekly_pnl_pct=weekly_ret,
                    atr_ratio=atr_ratio,
                )
                if not decision.allowed:
                    self.log.info("SKIP %s %s risk_filter=%s", date.date(), sym, decision.reason)
                    continue

                # TODO: earnings calendar filter hook can be added here.
                qty = self.risk.position_size(p.equity, signal.entry, signal.stop)
                if qty <= 0:
                    continue
                fill = self._apply_costs(signal.entry, is_buy=True)
                cost = qty * fill
                fee = max(bt.min_commission, bt.commission_per_share * qty)
                if cost + fee > p.cash:
                    self.log.info("SKIP %s %s insufficient_cash", date.date(), sym)
                    continue

                p.cash -= cost + fee
                p.positions[sym] = Position(sym, qty, fill, signal.stop, signal.target, date)
                self.log.info("ENTRY %s %s qty=%s entry=%.2f stop=%.2f reason=%s", date.date(), sym, qty, fill, signal.stop, signal.reason)

        equity_df = pd.DataFrame(curve, columns=["date", "equity"]).set_index("date")
        trades_df = pd.DataFrame(trades)
        metrics = performance_summary(equity_df["equity"], trades_df if not trades_df.empty else pd.DataFrame(columns=["pnl", "hold_days"]))

        out = Path("outputs")
        (out / "trades").mkdir(parents=True, exist_ok=True)
        (out / "equity").mkdir(parents=True, exist_ok=True)
        (out / "reports").mkdir(parents=True, exist_ok=True)
        (out / "plots").mkdir(parents=True, exist_ok=True)

        trades_df.to_csv(out / "trades" / "trades.csv", index=False)
        equity_df.to_csv(out / "equity" / "equity_curve.csv")
        pd.DataFrame([metrics]).to_csv(out / "reports" / "summary.csv", index=False)
        self._plot(equity_df, out / "plots" / "equity_drawdown.png")

        return {"metrics": metrics, "trades": trades_df, "equity": equity_df}

    def _apply_costs(self, px: float, is_buy: bool) -> float:
        slip = self.settings.backtest.slippage_bps / 10_000
        return px * (1 + slip if is_buy else 1 - slip)

    def _plot(self, equity_df: pd.DataFrame, path: Path) -> None:
        eq = equity_df["equity"]
        dd = (eq / eq.cummax()) - 1
        fig, ax = plt.subplots(2, 1, figsize=(10, 7), sharex=True)
        eq.plot(ax=ax[0], title="Equity Curve")
        dd.plot(ax=ax[1], title="Drawdown", color="red")
        fig.tight_layout()
        fig.savefig(path)
        plt.close(fig)
