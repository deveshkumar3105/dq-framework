from .base import Check, CheckResult
from engine.executors.registry import get_implementation


class UniquenessCheck(Check):
    def run(self, data) -> CheckResult:
        impl = get_implementation(self.engine_name, "uniqueness_check")
        dupes = impl(data, self.column)
        status = "pass" if dupes == 0 else "fail"
        return CheckResult("uniqueness_check", self.table, self.column, status, f"{dupes} duplicates found")