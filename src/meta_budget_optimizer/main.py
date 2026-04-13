from __future__ import annotations

import argparse
from typing import Any

from .budget_updater import BudgetUpdater
from .config import load_config
from .decision_engine import DecisionEngine
from .logging_setup import setup_logging
from .meta_client import MetaAdsClient
from .metrics_fetcher import MetricsFetcher
from .reporting import build_summary, export_actions_csv, notify_slack, save_summary
from .storage import get_last_action_times, init_db, store_actions, store_performance


def run_workflow(config_path: str) -> dict[str, Any]:
    cfg, runtime = load_config(config_path)
    logger = setup_logging(runtime.log_level)

    db_path = cfg["reporting"]["history_db_path"]
    init_db(db_path)
    last_actions = get_last_action_times(db_path)

    logger.info("Starting optimizer run", extra={"extra_data": {"mode": runtime.env_mode}})

    client = MetaAdsClient()
    ad_account_id = cfg["account"]["ad_account_id"]
    level = cfg["account"]["level"]

    fetcher = MetricsFetcher(client, ad_account_id, level)
    records = fetcher.fetch_multi_window(cfg["windows_days"])
    if not records:
        raise RuntimeError("No performance data returned by Meta API. Workflow stopped safely.")

    store_performance(db_path, records)

    engine = DecisionEngine(cfg, last_actions)
    decisions = engine.decide(records)

    updater = BudgetUpdater(client, runtime.env_mode, cfg)
    results = []
    for decision in decisions:
        result = updater.apply(decision)
        logger.info(
            "Processed decision",
            extra={"extra_data": {"decision": decision.__dict__, "result": result}},
        )
        results.append(result)

    store_actions(db_path, decisions)
    export_actions_csv(cfg["reporting"]["export_csv_path"], decisions, results)

    summary = build_summary(decisions, results, runtime.env_mode)
    save_summary(cfg["reporting"]["summary_output_path"], summary)

    if cfg["reporting"].get("notify_slack", False):
        notify_slack(summary, runtime.slack_webhook_url)

    logger.info("Optimizer run complete", extra={"extra_data": summary["totals"]})
    return summary


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Meta Ads budget optimizer")
    parser.add_argument("--config", default="config.example.yaml", help="Path to YAML config")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_workflow(args.config)
