import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logger() -> logging.Logger:
    log_directory = Path("logs")
    log_directory.mkdir(parents=True, exist_ok=True)
    log_file = log_directory / "energy_monitoring.log"

    logger = logging.getLogger("energy_monitoring")
    logger.setLevel(logging.INFO)
    logger.propagate = False

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,
            backupCount=7,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    return logger


"""
## FILE EXPLANATION
Purpose:
This file creates a reusable application logger.

Why this file exists:
Logging format and setup should be configured in one place and reused across
services and startup code.

What data enters the file:
No external input data. It configures Python logging internals.

What data leaves the file:
A configured Logger object used to print consistent logs.

Which layer of the architecture it belongs to:
Utility Layer.

How it interacts with other files:
main.py and service files call setup_logger() and use the returned logger.
"""
