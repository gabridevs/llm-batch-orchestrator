"""Hierarchical logging configuration with console and rotating-file handlers."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def configure_logging(
    log_directory: Path = Path("logs"),
    level: int = logging.INFO,
) -> logging.Logger:
    """Configure package logging without exposing prompts or credentials."""
    log_directory.mkdir(parents=True, exist_ok=True)
    package_logger = logging.getLogger("llm_orchestrator")
    package_logger.setLevel(level)
    package_logger.propagate = False

    configured_handlers = [
        handler
        for handler in package_logger.handlers
        if not isinstance(handler, logging.NullHandler)
    ]
    if configured_handlers:
        return package_logger

    for handler in list(package_logger.handlers):
        if isinstance(handler, logging.NullHandler):
            package_logger.removeHandler(handler)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(
        logging.Formatter("%(levelname)s %(name)s: %(message)s")
    )

    file_handler = RotatingFileHandler(
        log_directory / "orchestrator.log",
        maxBytes=250_000,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s %(name)s %(message)s",
        )
    )

    package_logger.addHandler(console_handler)
    package_logger.addHandler(file_handler)
    return package_logger
