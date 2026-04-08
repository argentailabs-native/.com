from __future__ import annotations

from dataclasses import dataclass, field

from swing_bot.portfolio.models import Position


@dataclass
class Portfolio:
    cash: float
    equity: float
    positions: dict[str, Position] = field(default_factory=dict)

    def open_risk_fraction(self) -> float:
        if self.equity <= 0:
            return 1.0
        total = 0.0
        for p in self.positions.values():
            total += max(p.entry_price - p.stop_price, 0) * p.qty
        return total / self.equity
