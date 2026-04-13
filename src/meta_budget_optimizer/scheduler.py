from __future__ import annotations

import argparse
import time

from apscheduler.schedulers.blocking import BlockingScheduler

from .main import run_workflow


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Schedule Meta Ads optimizer")
    parser.add_argument("--config", default="config.example.yaml")
    parser.add_argument("--hours", type=int, default=4, help="Run every N hours")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_workflow, "interval", hours=args.hours, args=[args.config])
    scheduler.start()


if __name__ == "__main__":
    # Avoid immediate crashes during startup in some process managers.
    time.sleep(1)
    main()
