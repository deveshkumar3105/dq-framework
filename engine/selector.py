import logging
from pathlib import Path

import yaml

from engine.connectors.pandas.csv import CSVConnector
from engine.connectors.spark.csv import SparkCSVConnector

logger = logging.getLogger(__name__)

DEFAULTS_PATH = Path(__file__).resolve().parent / "defaults.yaml"

CONNECTOR_MAP = {
    "pandas": CSVConnector,
    "spark": SparkCSVConnector,
}


def _load_defaults():
    with open(DEFAULTS_PATH) as f:
        return yaml.safe_load(f)


def decide_engine(config: dict, data_path: str) -> str:
    """Returns 'pandas' or 'spark' based on explicit config or auto-detection."""
    requested = config.get("engine", "auto")

    if requested in ("pandas", "spark"):
        logger.info("Engine explicitly set to '%s' in config", requested)
        return requested

    # auto-detection
    defaults = _load_defaults()
    threshold_mb = defaults.get("size_threshold_mb", 500)
    fallback = defaults.get("default_engine", "pandas")

    try:
        size_mb = Path(data_path).stat().st_size / (1024 * 1024)
    except FileNotFoundError:
        logger.warning("Could not read file size for %s, falling back to '%s'", data_path, fallback)
        return fallback

    if size_mb > threshold_mb:
        logger.info("Auto-detected engine='spark' (%.2fMB > %sMB threshold)", size_mb, threshold_mb)
        return "spark"

    logger.info("Auto-detected engine='pandas' (%.2fMB <= %sMB threshold)", size_mb, threshold_mb)
    return "pandas"


def get_connector_for_engine(engine_name: str):
    """Returns the connector class for the chosen engine."""
    return CONNECTOR_MAP[engine_name]