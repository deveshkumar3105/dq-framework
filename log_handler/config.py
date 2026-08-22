import logging

from .formatter import ColoredFormatter


def configure_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.StreamHandler()],
        force=True,
    )
    for handler in logging.getLogger().handlers:
        handler.setFormatter(ColoredFormatter("%(asctime)s %(levelname)s %(message)s"))