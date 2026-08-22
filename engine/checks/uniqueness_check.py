from .base import Check, CheckResult
from engine.executors.registry import get_implementation


class UniquenessCheck(Check):
    @property
    def rule_type(self) -> str:
        return "uniqueness_check"

    def run(self, data) -> CheckResult:
        impl = get_implementation(self.engine_name, "uniqueness_check")
        dupes = impl(data, self.column)
        status = "pass" if dupes == 0 else "fail"
        return CheckResult(
            rule_code=self.rule_code,
            rule_type=self.rule_type,
            table=self.table,
            column=self.column,
            status=status,
            details=f"{dupes} duplicates found",
        )