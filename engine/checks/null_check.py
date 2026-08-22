from .base import Check, CheckResult
from engine.executors.registry import get_implementation


class NullCheck(Check):
    @property
    def rule_type(self) -> str:
        return "null_check"

    def run(self, data) -> CheckResult:
        impl = get_implementation(self.engine_name, "null_check")
        null_count = impl(data, self.column)
        status = "pass" if null_count == 0 else "fail"
        return CheckResult(
            rule_code=self.rule_code,
            rule_type=self.rule_type,
            table=self.table,
            column=self.column,
            status=status,
            details=f"{null_count} nulls found",
        )