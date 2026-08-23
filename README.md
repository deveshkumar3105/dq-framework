# Data Quality Framework

A lightweight, config-driven data quality framework. Define checks (null, uniqueness, etc.) 
against tables in YAML, run them against pandas or Spark, and get structured, grouped, 
severity-tagged pass/fail results.

## What it does today

- Runs **null checks** and **uniqueness checks** against CSV data
- Supports **two execution engines**: pandas (default, for small/local data) and Spark (for larger data)
- **Auto-detects** which engine to use based on file size, or you can force one explicitly in config
- Config-driven: add checks by editing YAML, not code — each config is fully self-contained 
  (includes its own data source path)
- Checks support **multiple columns** per rule, or `"*"` to apply a rule to every column in the table
- Each rule can be tagged with a **severity** (`critical` or `warning`) — critical failures 
  log at ERROR level, warnings log at WARNING level
- Runs via CLI: `python -m engine.runner --config <path>`
- Colored console logging for readability
- Results are grouped per run and written to **per-table folders** under `results/`, 
  one file per run — see Results storage below

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
│   ├── utils.py             # Column resolution (explicit list vs "*")
│   ├── runner.py            # Orchestrates: config -> engine -> checks -> storage. CLI entrypoint.
│   ├── storage.py           # Writes results per run (per-table folder + legacy jsonl)
│   └── notifier.py          # Not yet implemented (currently commented out in runner)
├── configs/                 # One YAML per table, self-contained (includes data_path + checks)
│   └── sales/
├── data/                    # Sample CSVs used for local testing
├── results/                 # Generated run results, one subfolder per table (gitignored)
├── results.jsonl            # LEGACY - flat single-file results log (gitignored, being phased out)
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
engine: auto                    # "auto" | "pandas" | "spark"
data_path: data/orders.csv
checks:
  - type: null_check
    columns: [order_id]         # explicit list of columns
    severity: critical          # "critical" | "warning" (defaults to "warning" if omitted)
  - type: null_check
    columns: "*"                # applies this rule to every column in the table
    severity: warning
  - type: uniqueness_check
    columns: [order_id]
    severity: critical
```

### Columns
- A YAML list — e.g. `columns: [order_id, customer]` — applies the rule to each named column
- `"*"` — applies the rule to every column present in the loaded data at run time. 
  Resolved dynamically (via `engine/utils.py`), so it always reflects the table's actual 
  current schema, not a hardcoded list

### Severity
- `critical` — a failure logs at ERROR level
- `warning` (default) — a failure logs at WARNING level
- Currently affects logging only; does not yet block a run or pipeline (planned)

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

## Results storage

Each run writes a grouped JSON record containing every rule's result (including `rule_code`, 
`rule_type`, `column`, `status`, `severity`, `details`), to **two locations currently**:

**1. Primary — per-table folder structure (current standard):**
results/
├── orders/
│   └── 2026-08-24T09-12-05_a1b2c3d4.json
├── customers/
│   └── 2026-08-23T23-58-02_e5f6g7h8.json
One file per run, grouped by table folder, filename includes timestamp + short run ID.

**2. Legacy — `results.jsonl` (TODO: remove):**
A flat file at the project root, one line per run, kept temporarily alongside the new 
structure during the transition. **Do not build new tooling against this file** — it will 
be removed once the per-table structure is confirmed stable and nothing depends on the old format.

Example record shape (same shape written to both locations):
```json
{
  "run_id": "...",
  "table": "orders",
  "engine": "spark",
  "completed_at": "...",
  "rules": [
    {"rule_code": "orders.order_id.null_check", "rule_type": "null_check", "column": "order_id", "status": "fail", "severity": "critical", "details": "1 nulls found"}
  ]
}
```
`rule_code` is deterministic (`table.column.rule_type`), so the same logical rule can be 
tracked across multiple runs over time.

Both `results/` and `results.jsonl` are gitignored — they're generated output, not source.

## Known limitations (current state, not final design)

- **`results.jsonl` is legacy and dual-written temporarily** — see Results storage above; 
  will be removed once migration is confirmed complete
- **No database** — results live on the filesystem; no run history querying UI or dashboard yet 
  (a basic query/reader script is planned)
- **No notifier** — failures are logged to console only, no Slack/email integration yet
- **Severity doesn't block runs yet** — it only affects log level; blocking behavior is planned
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
- `utils.py` resolves column specs (`columns: [...]` or `columns: "*"`) before checks are built — 
  the `Check` classes themselves always operate on one resolved column, they're unaware `*` exists
- This split exists so adding a new engine, check, or config feature never requires touching 
  unrelated code