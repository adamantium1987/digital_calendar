# server/config/logger.py
"""
Centralized logging configuration
Replaces print() statements throughout the application
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
        log_dir: Optional[Path] = None,
        log_level: str = "INFO",
        console_output: bool = True
) -> logging.Logger:
    """
    Configure application-wide logging

    Args:
        log_dir: Directory for log files (None = logs to console only)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output to console

    Returns:
        Root logger instance
    """
    # Create root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear existing handlers
    root_logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler (rotating)
    if log_dir:
        log_dir = Path(log_dir)
        log_dir.mkdir(exist_ok=True)

        file_handler = RotatingFileHandler(
            log_dir / 'pi_calendar.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Separate error log
        error_handler = RotatingFileHandler(
            log_dir / 'pi_calendar_errors.log',
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger for a specific module

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)