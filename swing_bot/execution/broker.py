from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests


@dataclass
class OrderRequest:
    symbol: str
    qty: int
    side: str
    order_type: str = "market"
    time_in_force: str = "day"


class Broker(ABC):
    @abstractmethod
    def place_order(self, order: OrderRequest) -> dict:
        raise NotImplementedError


class AlpacaPaperBroker(Broker):
    def __init__(self, api_key: str, secret_key: str, base_url: str, enabled: bool = False):
        self.enabled = enabled
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({
            "APCA-API-KEY-ID": api_key,
            "APCA-API-SECRET-KEY": secret_key,
            "Content-Type": "application/json",
        })

    def place_order(self, order: OrderRequest) -> dict:
        if not self.enabled:
            return {"status": "skipped", "reason": "order_submission_disabled", "order": order.__dict__}
        payload = {
            "symbol": order.symbol,
            "qty": str(order.qty),
            "side": order.side,
            "type": order.order_type,
            "time_in_force": order.time_in_force,
        }
        r = self.session.post(f"{self.base_url}/v2/orders", json=payload, timeout=20)
        r.raise_for_status()
        return r.json()

    def get_account(self) -> dict:
        r = self.session.get(f"{self.base_url}/v2/account", timeout=20)
        r.raise_for_status()
        return r.json()

    def get_positions(self) -> list[dict]:
        r = self.session.get(f"{self.base_url}/v2/positions", timeout=20)
        r.raise_for_status()
        return r.json()
