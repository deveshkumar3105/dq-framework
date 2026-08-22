import json
from datetime import datetime

class ResultStorage:
    def __init__(self, path="results.jsonl"):
        self.path = path

    def save(self, result):
        record = {**result.__dict__, "timestamp": datetime.utcnow().isoformat()}
        with open(self.path, "a") as f:
            f.write(json.dumps(record) + "\n")