import argparse
import logging
from pathlib import Path

import yaml

from .checks.null_check import NullCheck
from .checks.uniqueness_check import UniquenessCheck
from .checks.custom_query_check import CustomQueryCheck
from .selector import decide_engine, get_connector_for_engine
from .storage import ResultStorage
from .utils import resolve_columns
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


def _run_table_checks(config: dict, engine_override_data_path: str):
    """Existing single-table, per-column check flow."""
    data_path = _resolve_path(config["data_path"])
    logger.info("Loaded config for table '%s' with %s check rules", config["table"], len(config.get("checks", [])))

    engine_name = decide_engine(config, data_path)
    connector_cls = get_connector_for_engine(engine_name)
    logger.info("Using engine '%s' for this run", engine_name)

    data = connector_cls(data_path).load()
    logger.info("Loaded data from %s using '%s' connector", data_path, engine_name)

    storage = ResultStorage()
    results = []

    rule_number = 0
    total_rules = sum(len(resolve_columns(data, rule["columns"])) for rule in config["checks"])

    for rule in config["checks"]:
        check_type = rule["type"]
        severity = rule.get("severity", "warning")
        resolved_columns = resolve_columns(data, rule["columns"])

        for column in resolved_columns:
            rule_number += 1
            logger.info(
                "Executing rule %s/%s: %s for column '%s' (severity=%s)",
                rule_number, total_rules, check_type, column, severity,
            )

            check_cls = CHECK_REGISTRY[check_type]
            check = check_cls(
                table=config["table"],
                column=column,
                engine_name=engine_name,
                severity=severity,
            )
            result = check.run(data)
            results.append(result)

            if result.status == "pass":
                logger.info("Rule %s/%s passed: %s (%s)", rule_number, total_rules, check_type, result.details)
            else:
                log_fn = logger.error if severity == "critical" else logger.warning
                log_fn("Rule %s/%s failed [%s]: %s (%s)", rule_number, total_rules, severity, check_type, result.details)
            # notifier.notify(result) TODO: Uncomment this line when Notifier is implemented

    storage.save_run(table=config["table"], engine=engine_name, results=results)


def _run_custom_checks(config: dict):
    """New flow: each entry loads its own named tables and runs a raw SQL query
    representing a violation-finding check across them (supports joins)."""
    storage = ResultStorage()

    for entry in config["custom_checks"]:
        name = entry["name"]
        severity = entry.get("severity", "warning")
        engine_name = entry.get("engine", "pandas")  # TODO: auto-detect based on table sizes
        connector_cls = get_connector_for_engine(engine_name)

        logger.info("Running custom check '%s' using engine '%s'", name, engine_name)

        tables = {}
        for table_name, table_path in entry["tables"].items():
            resolved_path = _resolve_path(table_path)
            tables[table_name] = connector_cls(resolved_path).load()
            logger.info("Loaded table '%s' from %s for custom check '%s'", table_name, resolved_path, name)

        query = entry.get("query")
        if not query and entry.get("query_file"):
            query_file_path = _resolve_path(entry["query_file"])
            with open(query_file_path) as f:
                query = f.read()

        if not query:
            raise ValueError(f"Custom check '{name}' has neither 'query' nor 'query_file' defined")

        check = CustomQueryCheck(name=name, query=query, engine_name=engine_name, severity=severity)
        result = check.run(tables)

        if result.status == "pass":
            logger.info("Custom check '%s' passed: %s", name, result.details)
        else:
            log_fn = logger.error if severity == "critical" else logger.warning
            log_fn("Custom check '%s' failed [%s]: %s", name, severity, result.details)
        # notifier.notify(result) TODO: Uncomment this line when Notifier is implemented

        storage.save_run(table=name, engine=engine_name, results=[result])


def run(config_path: str):
    configure_logging()
    config_path = _resolve_path(config_path)

    logger.info("Starting data quality run for %s", config_path)

    try:
        with open(config_path) as f:
            config = yaml.safe_load(f)

        if "custom_checks" in config:
            _run_custom_checks(config)
        else:
            _run_table_checks(config, config_path)

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