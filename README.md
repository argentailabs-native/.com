# Meta Ads Budget Optimization Workflow (Python)

Production-ready, conservative workflow for small agencies to monitor Meta Ads performance and reallocate budget safely.

## Folder structure

```text
.
├── .env.example
├── config.example.yaml
├── requirements.txt
├── README.md
├── data/
├── exports/
├── logs/
├── reports/
│   └── sample_output_report.json
└── src/
    └── meta_budget_optimizer/
        ├── __init__.py
        ├── budget_updater.py
        ├── config.py
        ├── decision_engine.py
        ├── logging_setup.py
        ├── main.py
        ├── meta_client.py
        ├── metrics_fetcher.py
        ├── reporting.py
        ├── scheduler.py
        └── storage.py
```

## How it works

1. Loads secure secrets from `.env` and business rules from YAML.
2. Pulls campaign/ad set/ad insights from Meta Ads API over rolling windows (3/7/14 days by default).
3. Applies configurable rules and guardrails:
   - minimum spend/impressions/clicks
   - CPA / ROAS / CTR / frequency checks
   - cooldown window to avoid frequent changes
   - max daily change cap + min/max budget rails
4. Runs in **recommendation** mode by default (dry-run).
5. In **live** mode, can post budget updates (or pause) through the Meta Graph API.
6. Saves history to SQLite, writes structured logs, and exports CSV + JSON summaries.

## Setup

### 1) Create virtualenv and install dependencies

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2) Configure environment secrets

```bash
cp .env.example .env
```

Fill values in `.env`:
- `META_ACCESS_TOKEN`: long-lived token with ads management access
- `META_APP_ID`: Meta app ID
- `META_APP_SECRET`: Meta app secret
- `META_AD_ACCOUNT_ID`: e.g. `act_1234567890`
- `META_API_VERSION`: e.g. `v20.0`

### 3) Configure business logic

Edit `config.example.yaml` thresholds and rules.

## Required Meta permissions / access

Your system user/token should have at least:
- `ads_read` (read performance insights)
- `ads_management` (required for live budget updates)
- Access to the target ad account in Business Manager

Notes:
- Some fields (e.g. `purchase_roas`) require purchase events + attribution data availability.
- Insights data can lag; very recent windows may be partial.
- API behavior/rate limits vary by app tier; retries/backoff are included.

## Run locally

### Dry-run (default)

```bash
python -m src.meta_budget_optimizer.main --config config.example.yaml
```

### Live execution (safety-gated)

1. Set `.env`: `EXECUTION_MODE=live`
2. In config, keep `require_live_confirmation: true`
3. Set `execution.live_confirmation_input` to exact `execution.live_confirmation_value`
4. Run same command:

```bash
python -m src.meta_budget_optimizer.main --config config.example.yaml
```

## Scheduler / cron

### APScheduler process (every 4 hours)

```bash
python -m src.meta_budget_optimizer.scheduler --config config.example.yaml --hours 4
```

### Cron example (every 4 hours)

```cron
0 */4 * * * cd /path/to/project && /path/to/.venv/bin/python -m src.meta_budget_optimizer.main --config config.example.yaml >> logs/cron.log 2>&1
```

## Outputs

- Structured logs: `logs/app.log`
- SQLite history: `data/history.db`
- Action CSV export: `exports/actions.csv`
- Latest summary JSON: `reports/latest_summary.json`
- Example report: `reports/sample_output_report.json`

## Safety defaults

- Dry-run by default
- No decision if data is insufficient
- No change above max daily percent
- No change below minimum daily budget
- Cooldown prevents frequent repeat edits
- Every action includes explicit reason logging
- If API returns no data, workflow aborts without changes
