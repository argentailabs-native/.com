from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .decision_engine import Decision
from .meta_client import MetaAdsClient


class BudgetUpdater:
    def __init__(self, client: MetaAdsClient, mode: str, config: dict[str, Any]) -> None:
        self.client = client
        self.mode = mode
        self.config = config

    def apply(self, decision: Decision) -> dict[str, Any]:
        result = {
            "entity_id": decision.entity_id,
            "action": decision.action,
            "executed": False,
            "api_response": None,
            "reason": decision.reason,
            "details": asdict(decision),
        }

        if decision.action == "no_change":
            result["reason"] = f"No update executed: {decision.reason}"
            return result

        if self.mode != "live":
            result["reason"] = f"Dry-run only: would execute {decision.action}. {decision.reason}"
            return result

        if self.config["execution"].get("require_live_confirmation", True):
            expected = self.config["execution"].get("live_confirmation_value")
            provided = self.config["execution"].get("live_confirmation_input")
            if not expected or provided != expected:
                result["reason"] = "Live mode blocked: live confirmation input missing or invalid"
                return result

        if decision.action == "pause":
            payload = {"status": "PAUSED"}
        else:
            cents = int(round(decision.new_budget * 100))
            if cents <= 0:
                result["reason"] = "Validation blocked budget update: new budget must be positive"
                return result
            payload = {"daily_budget": str(cents)}

        endpoint = decision.entity_id
        response = self.client.post(endpoint, payload)
        result["executed"] = True
        result["api_response"] = response
        return result
