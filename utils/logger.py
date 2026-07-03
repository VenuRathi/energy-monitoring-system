import logging


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("energy_monitoring")
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

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
