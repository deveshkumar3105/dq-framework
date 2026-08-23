from .base import CheckResult
from engine.executors.registry import get_implementation


class CustomQueryCheck:
    """A check that runs an arbitrary SQL query across one or more named tables.
    Does not extend the single-column Check base class, since it operates on
    multiple whole datasets rather than one column of one dataset.

    Convention: the query must return rows representing VIOLATIONS.
    Zero rows returned = pass. Any rows returned = fail."""

    def __init__(self, name: str, query: str, engine_name: str, severity: str = "warning"):
        self.name = name
        self.query = query
        self.engine_name = engine_name
        self.severity = severity

    @property
    def rule_type(self) -> str:
        return "custom_query_check"

    @property
    def rule_code(self) -> str:
        return f"custom.{self.name}.{self.rule_type}"

    def run(self, tables: dict) -> CheckResult:
        impl = get_implementation(self.engine_name, "custom_query_check")
        violation_count = impl(tables, self.query)
        status = "pass" if violation_count == 0 else "fail"
        return CheckResult(
            rule_code=self.rule_code,
            rule_type=self.rule_type,
            table=self.name,
            column="multiple",
            status=status,
            severity=self.severity,
            details=f"{violation_count} violating row(s) found",
        )