from __future__ import annotations

import argparse

from swing_bot.backtest.engine import BacktestEngine
from swing_bot.config.settings import load_settings
from swing_bot.data.screener import LiquidityScreener
from swing_bot.paper.engine import PaperTradingEngine
from swing_bot.reporting.report import write_summary
from swing_bot.utils.logger import setup_logger


def select_universe(settings, logger) -> list[str]:
    symbols = settings.universe.static_watchlist
    if not settings.universe.use_dynamic_scan:
        return symbols

    screener = LiquidityScreener(
        min_price=settings.universe.min_price,
        min_avg_volume=settings.universe.min_avg_volume,
        min_avg_dollar_volume=settings.universe.min_avg_dollar_volume,
        min_market_cap=settings.universe.min_market_cap,
    )
    result = screener.screen(symbols)
    for sym in result.passed:
        logger.info("SCREEN PASS %s", sym)
    for sym, reason in result.failed.items():
        logger.info("SCREEN FAIL %s reason=%s", sym, reason)
    return result.passed[: settings.universe.max_symbols]


def main() -> None:
    parser = argparse.ArgumentParser(description="Swing trading bot")
    parser.add_argument("--mode", choices=["backtest", "paper"], default="backtest")
    args = parser.parse_args()

    settings = load_settings()
    settings.runtime.mode = args.mode
    logger = setup_logger("swing_bot", settings.logging.level, settings.logging.log_dir, settings.logging.log_file)

    symbols = select_universe(settings, logger)
    logger.info("Universe size: %s", len(symbols))

    if args.mode == "backtest":
        engine = BacktestEngine(settings, logger)
        result = engine.run(symbols)
        logger.info("Metrics: %s", result["metrics"])
        write_summary(result["metrics"])
    else:
        engine = PaperTradingEngine(settings, logger)
        engine.run_once(symbols)


if __name__ == "__main__":
    main()
