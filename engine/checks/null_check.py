from .base import Check, CheckResult
from engine.executors.registry import get_implementation


class NullCheck(Check):
    def run(self, data) -> CheckResult:
        impl = get_implementation(self.engine_name, "null_check")
        null_count = impl(data, self.column)
        status = "pass" if null_count == 0 else "fail"
        return CheckResult("null_check", self.table, self.column, status, f"{null_count} nulls found")