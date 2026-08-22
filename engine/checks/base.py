from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CheckResult:
    rule_code: str
    rule_type: str
    table: str
    column: str
    status: str
    details: str = ""


class Check(ABC):
    def __init__(self, table: str, column: str, engine_name: str, **params):
        self.table = table
        self.column = column
        self.engine_name = engine_name
        self.params = params

    @property
    def rule_code(self) -> str:
        return f"{self.table}.{self.column}.{self.rule_type}"

    @property
    @abstractmethod
    def rule_type(self) -> str:
        pass

    @abstractmethod
    def run(self, data) -> CheckResult:
        pass