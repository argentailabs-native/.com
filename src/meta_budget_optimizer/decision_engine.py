from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from .metrics_fetcher import PerformanceRecord


@dataclass
class Decision:
    entity_id: str
    entity_name: str
    level: str
    action: str
    old_budget: float
    new_budget: float
    reason: str
    window_days: int


class DecisionEngine:
    def __init__(self, config: dict[str, Any], last_actions: dict[str, datetime]) -> None:
        self.config = config
        self.thresholds = config["thresholds"]
        self.rules = config["budget_rules"]
        self.cooldown_hours = config["execution"]["cooldown_hours"]
        self.last_actions = last_actions

    def decide(self, records: list[PerformanceRecord]) -> list[Decision]:
        records_by_entity: dict[str, list[PerformanceRecord]] = {}
        for row in records:
            records_by_entity.setdefault(row.entity_id, []).append(row)

        decisions: list[Decision] = []
        for entity_id, rows in records_by_entity.items():
            selected = max(rows, key=lambda r: r.window_days)
            if not self._has_enough_data(selected):
                decisions.append(self._no_change(selected, "insufficient sample size for safe decision"))
                continue

            if self._in_cooldown(entity_id):
                decisions.append(self._no_change(selected, "cooldown active; recently adjusted"))
                continue

            decision = self._decide_single(selected)
            decisions.append(decision)
        return decisions

    def _decide_single(self, row: PerformanceRecord) -> Decision:
        if row.cpa and row.cpa > self.thresholds["target_cpa"] * self.rules["pause_cpa_multiplier"] and row.spend >= self.rules["pause_min_spend"]:
            return self._action(row, "pause", 0.0, f"CPA {row.cpa:.2f} is far below efficiency target")

        if self._is_poor(row):
            target_budget = self._apply_change(row.daily_budget, -self.rules["decrease_pct"])
            reason = self._poor_reason(row)
            return self._action(row, "decrease_budget", target_budget, reason)

        if self._is_strong(row):
            target_budget = self._apply_change(row.daily_budget, self.rules["increase_pct"])
            return self._action(row, "increase_budget", target_budget, "strong CPA/ROAS with healthy conversion volume")

        return self._no_change(row, "performance within neutral band")

    def _is_poor(self, row: PerformanceRecord) -> bool:
        cpa_bad = row.cpa is not None and row.cpa > self.thresholds["target_cpa"] * self.thresholds["max_acceptable_cpa_multiplier"]
        roas_bad = row.roas is not None and row.roas < self.thresholds["min_roas"]
        ctr_bad = row.ctr is not None and row.ctr < self.thresholds["min_ctr"]
        high_spend = row.spend >= self.thresholds["min_spend"] * 2
        freq_bad = row.frequency is not None and row.frequency > self.thresholds["high_frequency_threshold"]
        return cpa_bad or roas_bad or (ctr_bad and high_spend) or freq_bad

    def _is_strong(self, row: PerformanceRecord) -> bool:
        cpa_good = row.cpa is not None and row.cpa <= self.thresholds["target_cpa"]
        roas_good = row.roas is not None and row.roas >= self.thresholds["min_roas"] * 1.2
        ctr_good = row.ctr is not None and row.ctr >= self.thresholds["min_ctr"] * 1.2
        enough_conv = row.conversions >= self.thresholds["min_conversions"]
        return enough_conv and ((cpa_good and ctr_good) or roas_good)

    def _has_enough_data(self, row: PerformanceRecord) -> bool:
        return all(
            [
                row.spend >= self.thresholds["min_spend"],
                row.impressions >= self.thresholds["min_impressions"],
                row.clicks >= self.thresholds["min_clicks"],
                row.window_days >= self.config["statistical_safety"]["min_days_data"],
            ]
        )

    def _in_cooldown(self, entity_id: str) -> bool:
        last_ts = self.last_actions.get(entity_id)
        if not last_ts:
            return False
        return datetime.now(timezone.utc) - last_ts < timedelta(hours=self.cooldown_hours)

    def _apply_change(self, current_budget: float, pct_delta: float) -> float:
        bounded_delta = max(-self.rules["max_change_pct_per_day"], min(self.rules["max_change_pct_per_day"], pct_delta))
        new_budget = current_budget * (1 + bounded_delta)
        new_budget = max(self.rules["min_daily_budget"], new_budget)
        new_budget = min(self.rules["max_daily_budget"], new_budget)
        return round(new_budget, 2)

    def _poor_reason(self, row: PerformanceRecord) -> str:
        reasons = []
        if row.cpa and row.cpa > self.thresholds["target_cpa"] * self.thresholds["max_acceptable_cpa_multiplier"]:
            reasons.append(f"CPA too high ({row.cpa:.2f})")
        if row.roas and row.roas < self.thresholds["min_roas"]:
            reasons.append(f"ROAS too low ({row.roas:.2f})")
        if row.ctr and row.ctr < self.thresholds["min_ctr"] and row.spend >= self.thresholds["min_spend"] * 2:
            reasons.append(f"CTR weak ({row.ctr:.2f}%) with high spend")
        if row.frequency and row.frequency > self.thresholds["high_frequency_threshold"]:
            reasons.append(f"frequency too high ({row.frequency:.2f})")
        return "; ".join(reasons) if reasons else "poor composite performance"

    @staticmethod
    def _action(row: PerformanceRecord, action: str, new_budget: float, reason: str) -> Decision:
        return Decision(
            entity_id=row.entity_id,
            entity_name=row.entity_name,
            level=row.level,
            action=action,
            old_budget=row.daily_budget,
            new_budget=new_budget,
            reason=reason,
            window_days=row.window_days,
        )

    @staticmethod
    def _no_change(row: PerformanceRecord, reason: str) -> Decision:
        return Decision(
            entity_id=row.entity_id,
            entity_name=row.entity_name,
            level=row.level,
            action="no_change",
            old_budget=row.daily_budget,
            new_budget=row.daily_budget,
            reason=reason,
            window_days=row.window_days,
        )
