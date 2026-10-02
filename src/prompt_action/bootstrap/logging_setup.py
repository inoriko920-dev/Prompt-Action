from __future__ import annotations

from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .app_paths import AppPaths


LOGGER_NAME = "prompt_action"


def configure_logging(paths: AppPaths) -> tuple[logging.Logger, Path]:
    log_file = paths.log_dir / f"prompt-action-{datetime.now():%Y%m%d}.log"
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    for handler in list(logger.handlers):
        handler.close()
        logger.removeHandler(handler)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=2 * 1024 * 1024,
        backupCount=7,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger, log_file


def flush_and_close(logger: logging.Logger) -> None:
    for handler in list(logger.handlers):
        try:
            handler.flush()
        finally:
            handler.close()
            logger.removeHandler(handler)
