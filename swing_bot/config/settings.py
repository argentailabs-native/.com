from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv

load_dotenv()


@dataclass
class BrokerConfig:
    provider: str = "alpaca"
    paper_only: bool = True
    enable_order_submission: bool = False
    base_url: str = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
    data_url: str = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets")
    api_key: str = os.getenv("ALPACA_API_KEY", "")
    secret_key: str = os.getenv("ALPACA_SECRET_KEY", "")


@dataclass
class UniverseConfig:
    use_dynamic_scan: bool = True
    static_watchlist: List[str] = field(default_factory=lambda: ["SPY", "QQQ", "IWM", "AAPL", "MSFT", "NVDA", "AMZN", "META", "GOOGL", "XLF", "XLV", "XLE"])
    min_price: float = 10.0
    min_avg_dollar_volume: float = 20_000_000
    min_avg_volume: int = 1_000_000
    min_market_cap: Optional[float] = None
    max_symbols: int = 60


@dataclass
class IndicatorConfig:
    sma_fast: int = 50
    sma_slow: int = 200
    rsi_period: int = 14
    rsi_min: float = 45.0
    rsi_max: float = 70.0
    macd_fast: int = 12
    macd_slow: int = 26
    macd_signal: int = 9
    atr_period: int = 14
    volume_lookback: int = 20


@dataclass
class RiskConfig:
    risk_per_trade: float = 0.0075
    max_concurrent_positions: int = 8
    max_portfolio_heat: float = 0.06
    max_daily_loss: float = 0.02
    max_weekly_loss: float = 0.05
    max_volatility_ratio: float = 0.08
    atr_stop_mult: float = 2.0
    trailing_atr_mult: float = 2.5
    rr_target: float = 2.0
    max_holding_days: int = 20
    allow_shorts: bool = False


@dataclass
class BacktestConfig:
    start_date: str = "2018-01-01"
    end_date: str = "2025-12-31"
    initial_capital: float = 100_000
    slippage_bps: float = 5.0
    commission_per_share: float = 0.005
    min_commission: float = 1.0


@dataclass
class RuntimeConfig:
    mode: str = "backtest"
    timezone: str = "America/New_York"
    evaluate_after_close_only: bool = True
    regime_filter_symbol: str = "SPY"
    retries: int = 3
    retry_delay_sec: int = 2


@dataclass
class LoggingConfig:
    level: str = "INFO"
    log_dir: Path = Path("outputs/logs")
    log_file: str = "swing_bot.log"


@dataclass
class Settings:
    broker: BrokerConfig = field(default_factory=BrokerConfig)
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    indicators: IndicatorConfig = field(default_factory=IndicatorConfig)
    risk: RiskConfig = field(default_factory=RiskConfig)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)
    runtime: RuntimeConfig = field(default_factory=RuntimeConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


def load_settings() -> Settings:
    return Settings()
