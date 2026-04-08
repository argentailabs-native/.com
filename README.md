# Swing Trading Bot (Python, Backtest + Paper Trading)

A production-structured, rule-based swing trading framework for highly liquid U.S. stocks/ETFs.

> **Important:** This project is for research and education. It does **not** guarantee profits. Start with backtesting and paper trading only.

## Features
- Modular architecture (data, strategy, risk, portfolio, execution, backtest, paper engine)
- Confluence-based long swing strategy:
  - Price > SMA50 > SMA200
  - RSI regime filter
  - MACD confirmation
  - Breakout/pullback continuation condition
  - Volume confirmation
- Risk controls:
  - Fixed fractional risk per trade
  - Position sizing by stop distance
  - Max positions and portfolio heat
  - Daily/weekly circuit breakers
  - Volatility filter
- Backtest outputs:
  - Trade log CSV, equity curve CSV
  - Performance summary CSV/JSON
  - Equity + drawdown plot
- Alpaca paper broker integration (live submission disabled by default)

## Project Structure
```text
swing_bot/
  config/settings.py
  data/data_provider.py
  data/screener.py
  indicators/ta.py
  strategy/swing_strategy.py
  risk/risk_manager.py
  portfolio/models.py
  portfolio/portfolio.py
  execution/broker.py
  backtest/engine.py
  backtest/metrics.py
  paper/engine.py
  reporting/report.py
  utils/logger.py
  main.py
tests/test_indicators.py
requirements.txt
.env.example
README.md
```

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Populate `.env` with Alpaca paper credentials.

## Run Backtest
```bash
python -m swing_bot.main --mode backtest
```

Outputs are saved in `outputs/`:
- `outputs/trades/trades.csv`
- `outputs/equity/equity_curve.csv`
- `outputs/reports/summary.csv`
- `outputs/reports/summary.json`
- `outputs/plots/equity_drawdown.png`

## Run Paper Trading (safe default)
By default, order submission is disabled (`enable_order_submission=False`).

```bash
python -m swing_bot.main --mode paper
```

To enable **paper** orders explicitly, set in `swing_bot/config/settings.py`:
- `paper_only=True`
- `enable_order_submission=True`

## Tuning Priorities (in order)
1. Universe quality (liquidity thresholds and watchlist quality)
2. Risk limits (`risk_per_trade`, heat cap, circuit breakers)
3. Exit logic (ATR stop/trailing and max holding days)
4. Entry strictness (RSI/MACD/volume thresholds)
5. Cost assumptions (slippage + commissions) to remain conservative

## Notes
- Strategy is deterministic and rule-based (no ML).
- Avoid curve fitting; validate on out-of-sample periods.
- Earnings/sector constraints have explicit extension points.
