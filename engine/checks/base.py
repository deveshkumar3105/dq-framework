from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class CheckResult:
    check_name: str
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

    @abstractmethod
    def run(self, data) -> CheckResult:
        pass