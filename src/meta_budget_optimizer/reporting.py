from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from .decision_engine import Decision


def export_actions_csv(path: str, decisions: list[Decision], results: list[dict[str, Any]]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "timestamp",
        "entity_id",
        "entity_name",
        "level",
        "action",
        "old_budget",
        "new_budget",
        "reason",
        "executed",
    ]

    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        now = datetime.now(timezone.utc).isoformat()
        for decision, result in zip(decisions, results):
            writer.writerow(
                {
                    "timestamp": now,
                    "entity_id": decision.entity_id,
                    "entity_name": decision.entity_name,
                    "level": decision.level,
                    "action": decision.action,
                    "old_budget": decision.old_budget,
                    "new_budget": decision.new_budget,
                    "reason": decision.reason,
                    "executed": result.get("executed", False),
                }
            )


def build_summary(decisions: list[Decision], results: list[dict[str, Any]], mode: str) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for d in decisions:
        counts[d.action] = counts.get(d.action, 0) + 1

    return {
        "run_ts": datetime.now(timezone.utc).isoformat(),
        "mode": mode,
        "totals": counts,
        "actions": [
            {
                "entity_id": d.entity_id,
                "entity_name": d.entity_name,
                "action": d.action,
                "old_budget": d.old_budget,
                "new_budget": d.new_budget,
                "reason": d.reason,
                "executed": results[idx].get("executed", False),
            }
            for idx, d in enumerate(decisions)
        ],
    }


def save_summary(path: str, summary: dict[str, Any]) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)


def notify_slack(summary: dict[str, Any], webhook_url: str | None) -> None:
    if not webhook_url:
        return
    text = (
        f"Meta budget optimizer run ({summary['mode']}): "
        f"{summary['totals']} actions at {summary['run_ts']}"
    )
    requests.post(webhook_url, json={"text": text}, timeout=10)
