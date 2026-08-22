import logging
from pathlib import Path

import yaml

from .checks.null_check import NullCheck
from .checks.uniqueness_check import UniquenessCheck
from .selector import decide_engine, get_connector_for_engine  # NEW
from .storage import ResultStorage
from log_handler.config import configure_logging 
# from .notifier import Notifier TODO: Uncomment this line when Notifier is implemented

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

CHECK_REGISTRY = {
    "null_check": NullCheck,
    "uniqueness_check": UniquenessCheck,
}


def _resolve_path(path: str) -> str:
    candidate = Path(path)
    if candidate.is_absolute():
        return str(candidate)

    project_candidate = PROJECT_ROOT / candidate
    if project_candidate.exists():
        return str(project_candidate)

    return str(candidate)



def run(config_path: str, data_path: str):
    configure_logging()
    config_path = _resolve_path(config_path)
    data_path = _resolve_path(data_path)

    logger.info("Starting data quality run for %s using %s", config_path, data_path)

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        logger.info("Loaded config for table '%s' with %s checks", config["table"], len(config.get("checks", [])))

        # NEW: decide which engine (pandas/spark) this job should run on
        engine_name = decide_engine(config, data_path)
        connector_cls = get_connector_for_engine(engine_name)
        logger.info("Using engine '%s' for this run", engine_name)

        data = connector_cls(data_path).load()
        logger.info("Loaded data from %s using '%s' connector", data_path, engine_name)

        storage = ResultStorage()
        # notifier = Notifier() TODO: Uncomment this line when Notifier is implemented

        for index, rule in enumerate(config["checks"], start=1):
            check_type = rule["type"]
            logger.info("Executing rule %s/%s: %s for column '%s'", index, len(config["checks"]), check_type, rule["column"])

            check_cls = CHECK_REGISTRY[check_type]
            # CHANGED: pass engine_name instead of instantiating with no engine context
            check = check_cls(table=config["table"], column=rule["column"], engine_name=engine_name)
            result = check.run(data)
            storage.save(result)

            if result.status == "pass":
                logger.info("Rule %s/%s passed: %s (%s)", index, len(config["checks"]), check_type, result.details)
            else:
                logger.warning("Rule %s/%s failed: %s (%s)", index, len(config["checks"]), check_type, result.details)
            # notifier.notify(result) TODO: Uncomment this line when Notifier is implemented

        logger.info("Completed data quality run for %s", config_path)
    except Exception:
        logger.exception("Data quality run failed for %s", config_path)
        raise


if __name__ == "__main__":
    jobs = [
        ("configs/sales/orders.yaml", "data/orders.csv"),
        ("configs/sales/customers.yaml", "data/customers.csv"),
    ]
    for config_path, data_path in jobs:
        run(config_path, data_path)