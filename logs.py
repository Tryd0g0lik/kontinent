# logs.py
"""
This module provides logging configuration.
Logs are output to both console and a log file (default: 'log_putout.log').
"""

import logging
import threading
import time
from typing import Optional


def configure_logging(
    level: int = logging.INFO, log_file: str = "log_putout.log"
) -> None:
    """
    Initialize logging configuration.

    Args:
        level: Logging level (default: logging.INFO)
        log_file: Name of the log file (default: 'log_putout.log')

    Example:
        import logging
        from rabbit.logs import configure_logging
        log = logging.getLogger(__name__)
        configure_logging(logging.INFO)
        log.info("Application started")
    """
    # Clear any existing handlers
    logging.getLogger().handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        "[%(asctime)s.%(msecs)03d] %(levelname)s - %(name)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S.%u",
    )

    # File handler
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # Configure root logger
    logging.basicConfig(
        level=level, handlers=[file_handler, console_handler], force=True
    )

    # Start log file maintenance thread
    threading.Thread(
        target=check_log_file, args=(log_file,), daemon=True, name="LogFileMaintenance"
    ).start()


def check_log_file(
    log_file: str, max_lines: int = 3000, check_interval: int = 1800
) -> None:
    """
    Check log file size and rotate if needed.

    Args:
        log_file: Path to log file
        max_lines: Maximum lines before rotation (default: 3000)
        check_interval: Check interval in seconds (default: 1800 = 30 min)
    """
    while True:
        time.sleep(check_interval)
        try:
            with open(log_file, "r+", encoding="utf-8") as f:
                lines = f.readlines()
                if len(lines) >= max_lines:
                    f.seek(0)
                    f.truncate()
                    logging.warning(
                        "Log file %s was cleared (%d lines exceeded limit of %d)",
                        log_file,
                        len(lines),
                        max_lines,
                    )
        except Exception as e:
            logging.error("Error checking log file: %s", str(e), exc_info=True)


class Logger:
    """Utility class for logging operations."""

    @staticmethod
    def get_class_name(obj: object) -> str:
        """Get class name of an object."""
        return obj.__class__.__name__
