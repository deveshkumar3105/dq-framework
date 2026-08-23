import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

# TODO: results.jsonl is the legacy single-file storage format, kept temporarily
# alongside the new results/<table>/<run>.json structure for a transition period.
# Once the new structure is confirmed reliable and any tooling/scripts depending on
# results.jsonl have been migrated, remove save-to-jsonl entirely (see save_run below).


class ResultStorage:
    def __init__(self, base_dir="results", legacy_path="results.jsonl"):
        self.base_dir = Path(base_dir)
        self.legacy_path = Path(legacy_path)

    def save_run(self, table: str, engine: str, results: list):
        run_id = str(uuid.uuid4())
        completed_at = datetime.now(timezone.utc)

        record = {
            "run_id": run_id,
            "table": table,
            "engine": engine,
            "completed_at": completed_at.isoformat(),
            "rules": [asdict(r) for r in results],
        }

        file_path = self._save_to_table_folder(table, run_id, completed_at, record)
        self._save_to_legacy_file(record)  # TODO: remove once results.jsonl is deprecated

        return file_path

    def _save_to_table_folder(self, table: str, run_id: str, completed_at: datetime, record: dict) -> Path:
        table_dir = self.base_dir / table
        table_dir.mkdir(parents=True, exist_ok=True)

        timestamp_str = completed_at.strftime("%Y-%m-%dT%H-%M-%S")
        run_id_short = run_id.split("-")[0]
        filename = f"{timestamp_str}_{run_id_short}.json"

        file_path = table_dir / filename
        with open(file_path, "w") as f:
            json.dump(record, f, indent=2)

        return file_path

    def _save_to_legacy_file(self, record: dict):
        # TODO: remove this method and its call in save_run() once results.jsonl is deprecated
        with open(self.legacy_path, "a") as f:
            f.write(json.dumps(record) + "\n")