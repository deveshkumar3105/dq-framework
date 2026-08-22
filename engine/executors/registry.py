from engine.executors.pandas import null_check as pandas_null_check
from engine.executors.pandas import uniqueness_check as pandas_uniqueness_check
from engine.executors.spark import null_check as spark_null_check
from engine.executors.spark import uniqueness_check as spark_uniqueness_check

IMPLEMENTATIONS = {
    ("pandas", "null_check"): pandas_null_check.run,
    ("pandas", "uniqueness_check"): pandas_uniqueness_check.run,
    ("spark", "null_check"): spark_null_check.run,
    ("spark", "uniqueness_check"): spark_uniqueness_check.run,
}


def get_implementation(engine_name: str, check_type: str):
    key = (engine_name, check_type)
    if key not in IMPLEMENTATIONS:
        raise NotImplementedError(f"No '{check_type}' implementation for engine '{engine_name}'")
    return IMPLEMENTATIONS[key]