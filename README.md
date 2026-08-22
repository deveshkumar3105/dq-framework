# Data Quality Framework

A lightweight, config-driven data quality framework. Define checks (null, uniqueness, etc.) 
against tables in YAML, run them against pandas or Spark, and get structured, grouped pass/fail 
results with logging.

## What it does today

- Runs **null checks** and **uniqueness checks** against CSV data
- Supports **two execution engines**: pandas (default, for small/local data) and Spark (for larger data)
- **Auto-detects** which engine to use based on file size, or you can force one explicitly in config
- Config-driven: add checks by editing YAML, not code — each config is fully self-contained 
  (includes its own data source path)
- Runs via CLI: `python -m engine.runner --config <path>`
- Colored console logging for readability
- Results grouped by run and persisted to `results.jsonl` — one JSON record per table run, 
  containing all rule results nested inside, each with a stable `rule_code`

## Project structure

dq-framework/
├── engine/
│   ├── checks/              # Check definitions (engine-agnostic) - null_check, uniqueness_check
│   ├── connectors/
│   │   ├── pandas/          # Loads data via pandas
│   │   └── spark/           # Loads data via Spark
│   ├── executors/
│   │   ├── pandas/          # Per-check pandas implementation
│   │   ├── spark/           # Per-check Spark implementation
│   │   └── registry.py      # Maps (engine, check_type) -> implementation
│   ├── selector.py          # Decides pandas vs spark per run (explicit or auto)
│   ├── defaults.yaml        # Auto-detection thresholds
│   ├── runner.py            # Orchestrates: config -> engine -> checks -> storage. CLI entrypoint.
│   ├── storage.py           # Writes one grouped record per run to results.jsonl
│   └── notifier.py          # Not yet implemented (currently commented out in runner)
├── configs/                 # One YAML per table, self-contained (includes data_path + checks)
│   └── sales/
├── data/                    # Sample CSVs used for local testing
├── log_handler/             # Logging setup + colored formatter, separate from runner
├── tests/
│   └── unit/                # Minimal — mostly TODO (see Limitations)
├── docs/                    # Placeholder, not yet written
├── ci/                      # Placeholder, not yet implemented
└── requirements.txt

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

Each config is self-contained — it declares its own table name, engine preference, 
data source, and checks. Run one config at a time via the `--config` flag:

```bash
python -m engine.runner --config configs/sales/orders.yaml
```

**Important:** always run as a module (`python -m engine.runner`) from the project root — 
never run `runner.py` directly, since it uses relative imports that require this invocation style.

To run multiple configs, loop at the shell level for now (a `--config-dir` flag is planned):

```bash
for f in configs/sales/*.yaml; do
  python -m engine.runner --config "$f"
done
```

## Config format

```yaml
table: orders
engine: auto              # "auto" | "pandas" | "spark"
data_path: data/orders.csv
checks:
  - type: null_check
    column: order_id
  - type: uniqueness_check
    column: order_id
```

## Adding a new check to an existing table

Add an entry under `checks:` in the relevant YAML — no code changes needed for existing check types.

## Adding a brand-new check type (e.g. freshness_check)

1. Add `engine/checks/freshness_check.py` — defines the check's pass/fail logic (engine-agnostic), 
   sets `rule_type`
2. Add `engine/executors/pandas/freshness_check.py` — pandas implementation
3. Add `engine/executors/spark/freshness_check.py` — Spark implementation
4. Register both in `engine/executors/registry.py`
5. Register the check class in `CHECK_REGISTRY` inside `runner.py`

This is deliberately spread across small files rather than one large file, so adding a check 
never requires editing existing check code.

## Engine selection

Set explicitly per table in its YAML (`engine: pandas` or `engine: spark`), or omit/set to 
`auto` to let `selector.py` decide based on file size, using thresholds in `engine/defaults.yaml`:
```yaml
size_threshold_mb: 500
default_engine: pandas
```

## Results format

Each run produces one grouped JSON record in `results.jsonl`:
```json
{
  "run_id": "...",
  "table": "orders",
  "engine": "spark",
  "completed_at": "...",
  "rules": [
    {"rule_code": "orders.order_id.null_check", "rule_type": "null_check", "column": "order_id", "status": "fail", "details": "1 nulls found"},
    {"rule_code": "orders.order_id.uniqueness_check", "rule_type": "uniqueness_check", "column": "order_id", "status": "fail", "details": "1 duplicates found"}
  ]
}
```
`rule_code` is deterministic (`table.column.rule_type`), so the same logical rule can be 
tracked across multiple runs over time.

## Known limitations (current state, not final design)

- **No database** — results are stored in a flat `results.jsonl` file, no run history querying UI, 
  no dashboard (a basic query/reader script is planned)
- **No notifier** — failures are logged to console only, no Slack/email integration yet
- **One config per CLI run** — no directory auto-discovery yet (`--config-dir` planned)
- **Only two check types** exist so far: null_check, uniqueness_check
- **Only CSV sources** supported — database connectors (Oracle, Snowflake) are planned, 
  will be referenced via a `connections.yaml` + connection name rather than embedded credentials
- **Dependency versions unpinned** — pinning planned once versions are confirmed stable
- **Minimal test coverage** — per-check and per-executor unit tests are still TODO
- **`docs/` and `ci/` are placeholders** — not yet written

## Design notes for contributors

- `checks/` defines *what* a check means (pass/fail semantics, rule_code generation) — engine-agnostic
- `executors/` defines *how* to compute a check on a specific engine — one file per check, per engine
- `connectors/` defines *how* to load data for a specific engine
- `selector.py` is the only place that decides which engine runs a given job
- This split exists so adding a new engine or a new check never requires touching unrelated code
Push it
bashcd ~/Documents/DataEngineeringProject/DataQuality/dq-framework
git add README.md
git commit -m "docs: update README with CLI usage, config format, and current limitations"
git push
