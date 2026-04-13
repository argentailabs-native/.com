from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from .meta_client import MetaAdsClient


@dataclass
class PerformanceRecord:
    entity_id: str
    entity_name: str
    level: str
    window_days: int
    spend: float
    impressions: int
    clicks: int
    conversions: float
    cpa: float | None
    ctr: float | None
    cpc: float | None
    roas: float | None
    frequency: float | None
    daily_budget: float
    status: str


class MetricsFetcher:
    def __init__(self, client: MetaAdsClient, ad_account_id: str, level: str) -> None:
        self.client = client
        self.ad_account_id = ad_account_id.replace("act_", "")
        self.level = level

    def fetch_multi_window(self, windows: list[int]) -> list[PerformanceRecord]:
        rows: list[PerformanceRecord] = []
        for days in windows:
            rows.extend(self._fetch_for_window(days))
        return rows

    def _fetch_for_window(self, days: int) -> list[PerformanceRecord]:
        fields = [
            "campaign_id",
            "campaign_name",
            "adset_id",
            "adset_name",
            "ad_id",
            "ad_name",
            "spend",
            "impressions",
            "clicks",
            "actions",
            "action_values",
            "frequency",
            "ctr",
            "cpc",
            "purchase_roas",
            "daily_budget",
            "effective_status",
        ]

        from datetime import date, timedelta

        since_date = (date.today() - timedelta(days=days)).isoformat()
        until_date = date.today().isoformat()

        params: dict[str, Any] = {
            "level": self.level,
            "fields": ",".join(fields),
            "time_range": json.dumps({"since": since_date, "until": until_date}),
            "limit": 500,
        }
        endpoint = f"act_{self.ad_account_id}/insights"
        raw = self.client.get(endpoint, params)
        data = raw.get("data", [])

        parsed: list[PerformanceRecord] = []
        for item in data:
            parsed.append(self._parse_row(item, days))
        return parsed

    def _parse_row(self, item: dict[str, Any], days: int) -> PerformanceRecord:
        conversions = self._extract_actions(item.get("actions", []), ["offsite_conversion", "lead", "purchase"])
        roas = self._extract_roas(item)
        spend = float(item.get("spend", 0.0))
        cpa = (spend / conversions) if conversions > 0 else None

        level_mapping = {
            "campaign": ("campaign_id", "campaign_name"),
            "adset": ("adset_id", "adset_name"),
            "ad": ("ad_id", "ad_name"),
        }
        id_key, name_key = level_mapping[self.level]

        return PerformanceRecord(
            entity_id=item.get(id_key, ""),
            entity_name=item.get(name_key, "unknown"),
            level=self.level,
            window_days=days,
            spend=spend,
            impressions=int(float(item.get("impressions", 0))),
            clicks=int(float(item.get("clicks", 0))),
            conversions=conversions,
            cpa=cpa,
            ctr=float(item["ctr"]) if item.get("ctr") else None,
            cpc=float(item["cpc"]) if item.get("cpc") else None,
            roas=roas,
            frequency=float(item["frequency"]) if item.get("frequency") else None,
            daily_budget=float(item.get("daily_budget", 0.0)) / 100 if item.get("daily_budget") else 0.0,
            status=item.get("effective_status", "UNKNOWN"),
        )

    @staticmethod
    def _extract_actions(actions: list[dict[str, Any]], action_types: list[str]) -> float:
        total = 0.0
        for action in actions:
            action_type = action.get("action_type", "")
            if any(term in action_type for term in action_types):
                total += float(action.get("value", 0.0))
        return total

    @staticmethod
    def _extract_roas(item: dict[str, Any]) -> float | None:
        roas_list = item.get("purchase_roas") or []
        if roas_list and isinstance(roas_list, list):
            return float(roas_list[0].get("value", 0.0))

        values = item.get("action_values") or []
        revenue = 0.0
        for value in values:
            if "purchase" in value.get("action_type", ""):
                revenue += float(value.get("value", 0.0))

        spend = float(item.get("spend", 0.0))
        if spend <= 0:
            return None
        return revenue / spend if revenue > 0 else None
