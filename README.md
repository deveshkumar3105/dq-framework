## Setup

```bash
cd dq-framework
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Spark checks additionally require a local JVM (JDK 11 or 17) and `pyspark` installed — 
run `java -version` to confirm before using `engine: spark` in a config.

## How to run

Jobs are currently defined as a hardcoded list at the bottom of `runner.py`:

```python
if __name__ == "__main__":
    jobs = [
        ("configs/sales/orders.yaml", "data/orders.csv"),
        ("configs/sales/customers.yaml", "data/customers.csv"),
    ]
```

Run all configured jobs:
```bash
python -m engine.runner
```

**Important:** always run as a module (`python -m engine.runner`) from the project root — 
never run `runner.py` directly, since it uses relative imports that require this invocation style.

## Adding a new check to an existing table

Edit the relevant YAML in `configs/`, e.g. `configs/sales/orders.yaml`:

```yaml
table: orders
engine: auto        # "auto" | "pandas" | "spark"
checks:
  - type: null_check
    column: order_id
  - type: uniqueness_check
    column: order_id
```

No code changes needed for existing check types — just add entries under `checks:`.

## Adding a brand-new check type (e.g. freshness_check)

1. Add `engine/checks/freshness_check.py` — defines the check's pass/fail logic (engine-agnostic)
2. Add `engine/executors/pandas/freshness_check.py` — pandas implementation
3. Add `engine/executors/spark/freshness_check.py` — Spark implementation
4. Register both in `engine/executors/registry.py`
5. Register the check class in `CHECK_REGISTRY` inside `runner.py`

This is deliberately spread across small files rather than one large file, so adding a check 
never requires editing existing check code.

## Engine selection

Set explicitly per table in its YAML:
```yaml
engine: pandas   # or: spark
```

Or omit the field (or set `engine: auto`) to let `selector.py` decide based on file size, 
using thresholds in `engine/defaults.yaml`:
```yaml
size_threshold_mb: 500
default_engine: pandas
```

## Known limitations (current state, not final design)

- **No database** — results are stored in a flat `results.jsonl` file, no run history querying, 
  no dashboard
- **No notifier** — failures are logged to console only, no Slack/email integration yet 
  (`notifier.py` exists but is unused)
- **Jobs are hardcoded** in `runner.py` — no auto-discovery of configs yet
- **Only two check types** exist so far: null_check, uniqueness_check
- **Only CSV sources** supported — no Postgres/Snowflake connector yet
- **No `run_id`** — results from different runs aren't grouped, making it hard to tell 
  which results belong to which execution
- **Minimal test coverage** — only one test file exists so far (`tests/unit/test_runner_logging.py`); 
  per-check and per-executor unit tests are still TODO
- **`docs/` and `ci/` are placeholders** — not yet written

## Design notes for contributors

- `checks/` defines *what* a check means (pass/fail semantics) — engine-agnostic
- `executors/` defines *how* to compute a check on a specific engine — one file per check, per engine
- `connectors/` defines *how* to load data for a specific engine
- `selector.py` is the only place that decides which engine runs a given job
- This split exists so adding a new engine or a new check never requires touching unrelated code
EOF