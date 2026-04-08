from __future__ import annotations

from swing_bot.config.settings import Settings
from swing_bot.data.data_provider import YFinanceDataProvider
from swing_bot.execution.broker import AlpacaPaperBroker, OrderRequest
from swing_bot.strategy.swing_strategy import SwingTrendStrategy


class PaperTradingEngine:
    def __init__(self, settings: Settings, logger):
        self.settings = settings
        self.log = logger
        self.broker = AlpacaPaperBroker(
            api_key=settings.broker.api_key,
            secret_key=settings.broker.secret_key,
            base_url=settings.broker.base_url,
            enabled=settings.broker.enable_order_submission and settings.broker.paper_only,
        )
        self.data = YFinanceDataProvider(cache_dir="cache")
        self.strategy = SwingTrendStrategy(settings.indicators, settings.risk)

    def run_once(self, symbols: list[str]) -> None:
        acct = self.broker.get_account()
        self.log.info("ACCOUNT equity=%s cash=%s", acct.get("equity"), acct.get("cash"))

        for sym in symbols:
            df = self.data.get_history(sym, "2023-01-01", "2030-01-01")
            if len(df) < 220:
                continue
            signal = self.strategy.entry_signal(sym, df)
            if signal:
                self.log.info("PAPER SIGNAL %s %s", sym, signal.reason)
                order = OrderRequest(symbol=sym, qty=1, side="buy")
                resp = self.broker.place_order(order)
                self.log.info("ORDER RESP %s", resp)
