from __future__ import annotations

import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from .decision_engine import Decision
from .metrics_fetcher import PerformanceRecord


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS performance_history (
                run_ts TEXT,
                entity_id TEXT,
                entity_name TEXT,
                level TEXT,
                window_days INTEGER,
                spend REAL,
                impressions INTEGER,
                clicks INTEGER,
                conversions REAL,
                cpa REAL,
                ctr REAL,
                cpc REAL,
                roas REAL,
                frequency REAL,
                daily_budget REAL,
                status TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS action_history (
                run_ts TEXT,
                entity_id TEXT,
                entity_name TEXT,
                level TEXT,
                action TEXT,
                old_budget REAL,
                new_budget REAL,
                reason TEXT,
                window_days INTEGER
            )
            """
        )


def store_performance(db_path: str, rows: list[PerformanceRecord]) -> None:
    run_ts = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO performance_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_ts,
                    r.entity_id,
                    r.entity_name,
                    r.level,
                    r.window_days,
                    r.spend,
                    r.impressions,
                    r.clicks,
                    r.conversions,
                    r.cpa,
                    r.ctr,
                    r.cpc,
                    r.roas,
                    r.frequency,
                    r.daily_budget,
                    r.status,
                )
                for r in rows
            ],
        )


def store_actions(db_path: str, decisions: list[Decision]) -> None:
    run_ts = datetime.now(timezone.utc).isoformat()
    with sqlite3.connect(db_path) as conn:
        conn.executemany(
            """
            INSERT INTO action_history VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_ts,
                    d.entity_id,
                    d.entity_name,
                    d.level,
                    d.action,
                    d.old_budget,
                    d.new_budget,
                    d.reason,
                    d.window_days,
                )
                for d in decisions
            ],
        )


def get_last_action_times(db_path: str) -> dict[str, datetime]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(
            """
            SELECT entity_id, MAX(run_ts) AS last_ts
            FROM action_history
            WHERE action != 'no_change'
            GROUP BY entity_id
            """
        )
        rows = cur.fetchall()

    output: dict[str, datetime] = {}
    for entity_id, ts in rows:
        output[entity_id] = datetime.fromisoformat(ts)
    return output


def decision_to_dict(decision: Decision) -> dict:
    return asdict(decision)
