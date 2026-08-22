import json
import uuid
from dataclasses import asdict
from datetime import datetime, timezone


class ResultStorage:
    def __init__(self, path="results.jsonl"):
        self.path = path

    def save_run(self, table: str, engine: str, results: list):
        record = {
            "run_id": str(uuid.uuid4()),
            "table": table,
            "engine": engine,
            "completed_at": datetime.now(timezone.utc).isoformat(),
            "rules": [asdict(r) for r in results],
        }
        with open(self.path, "a") as f:
            f.write(json.dumps(record) + "\n")