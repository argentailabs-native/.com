from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RiskDecision:
    allowed: bool
    reason: str


class RiskManager:
    def __init__(self, risk_per_trade: float, max_positions: int, max_portfolio_heat: float, max_daily_loss: float, max_weekly_loss: float, max_volatility_ratio: float):
        self.risk_per_trade = risk_per_trade
        self.max_positions = max_positions
        self.max_portfolio_heat = max_portfolio_heat
        self.max_daily_loss = max_daily_loss
        self.max_weekly_loss = max_weekly_loss
        self.max_volatility_ratio = max_volatility_ratio

    def position_size(self, equity: float, entry: float, stop: float) -> int:
        per_share_risk = max(entry - stop, 0)
        if per_share_risk <= 0:
            return 0
        risk_budget = equity * self.risk_per_trade
        qty = int(risk_budget // per_share_risk)
        return max(qty, 0)

    def can_open(self, open_positions: int, open_risk: float, daily_pnl_pct: float, weekly_pnl_pct: float, atr_ratio: float) -> RiskDecision:
        if open_positions >= self.max_positions:
            return RiskDecision(False, "max_concurrent_positions")
        if open_risk >= self.max_portfolio_heat:
            return RiskDecision(False, "max_portfolio_heat")
        if daily_pnl_pct <= -self.max_daily_loss:
            return RiskDecision(False, "daily_loss_circuit_breaker")
        if weekly_pnl_pct <= -self.max_weekly_loss:
            return RiskDecision(False, "weekly_loss_circuit_breaker")
        if atr_ratio > self.max_volatility_ratio:
            return RiskDecision(False, "volatility_too_high")
        return RiskDecision(True, "ok")
