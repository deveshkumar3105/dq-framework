import argparse
import logging
from pathlib import Path

import yaml

from .checks.null_check import NullCheck
from .checks.uniqueness_check import UniquenessCheck
from .selector import decide_engine, get_connector_for_engine
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


def run(config_path: str):
    configure_logging()
    config_path = _resolve_path(config_path)

    logger.info("Starting data quality run for %s", config_path)

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        data_path = _resolve_path(config["data_path"])
        logger.info("Loaded config for table '%s' with %s checks", config["table"], len(config.get("checks", [])))

        engine_name = decide_engine(config, data_path)
        connector_cls = get_connector_for_engine(engine_name)
        logger.info("Using engine '%s' for this run", engine_name)

        data = connector_cls(data_path).load()
        logger.info("Loaded data from %s using '%s' connector", data_path, engine_name)

        storage = ResultStorage()
        results = []  # CHANGED: collect results instead of saving immediately
        # notifier = Notifier() TODO: Uncomment this line when Notifier is implemented

        for index, rule in enumerate(config["checks"], start=1):
            check_type = rule["type"]
            logger.info("Executing rule %s/%s: %s for column '%s'", index, len(config["checks"]), check_type, rule["column"])

            check_cls = CHECK_REGISTRY[check_type]
            check = check_cls(table=config["table"], column=rule["column"], engine_name=engine_name)
            result = check.run(data)
            results.append(result)  # CHANGED: no longer storage.save(result) here

            if result.status == "pass":
                logger.info("Rule %s/%s passed: %s (%s)", index, len(config["checks"]), check_type, result.details)
            else:
                logger.warning("Rule %s/%s failed: %s (%s)", index, len(config["checks"]), check_type, result.details)
            # notifier.notify(result) TODO: Uncomment this line when Notifier is implemented

        storage.save_run(table=config["table"], engine=engine_name, results=results)  # NEW: batched write, step 5
        logger.info("Completed data quality run for %s", config_path)
    except Exception:
        logger.exception("Data quality run failed for %s", config_path)
        raise


def main():
    parser = argparse.ArgumentParser(description="Run data quality checks against a config file")
    parser.add_argument("--config", required=True, help="Path to the table's YAML config file")
    args = parser.parse_args()
    run(args.config)


if __name__ == "__main__":
    main()