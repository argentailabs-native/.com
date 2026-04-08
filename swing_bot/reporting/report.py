from __future__ import annotations

import json
from pathlib import Path


def write_summary(metrics: dict, path: str = "outputs/reports/summary.json") -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
