"""
Structured logging configuration with JSON support

This module provides structured logging capabilities with JSON output
for better log aggregation and analysis in production.
"""

from __future__ import annotations

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler


class JSONFormatter(logging.Formatter):
    """
    JSON log formatter for structured logging

    Outputs logs in JSON format for easy parsing by log aggregation tools.
    """

    def __init__(
        self,
        service_name: str = "digital-calendar",
        environment: str = "production",
        include_extra: bool = True
    ):
        super().__init__()
        self.service_name = service_name
        self.environment = environment
        self.include_extra = include_extra

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
        }

        # Add source location
        log_data["source"] = {
            "file": record.pathname,
            "line": record.lineno,
            "function": record.funcName,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info) if record.exc_info else None,
            }

        # Add extra fields
        if self.include_extra and hasattr(record, '__dict__'):
            # Get all extra attributes
            reserved_attrs = {
                'name', 'msg', 'args', 'created', 'filename', 'funcName',
                'levelname', 'levelno', 'lineno', 'module', 'msecs', 'message',
                'pathname', 'process', 'processName', 'relativeCreated', 'thread',
                'threadName', 'exc_info', 'exc_text', 'stack_info'
            }

            extra = {
                k: v for k, v in record.__dict__.items()
                if k not in reserved_attrs and not k.startswith('_')
            }

            if extra:
                log_data["extra"] = extra

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """
    Colored console formatter for development

    Provides color-coded log output for better readability in development.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        color = self.COLORS.get(record.levelname, self.RESET)

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Build formatted message
        log_msg = (
            f"{color}{self.BOLD}[{record.levelname}]{self.RESET} "
            f"{timestamp} - "
            f"{color}{record.name}{self.RESET} - "
            f"{record.getMessage()}"
        )

        # Add source location for warnings and errors
        if record.levelno >= logging.WARNING:
            log_msg += f"\n  {self.COLORS['DEBUG']}→ {record.pathname}:{record.lineno}{self.RESET}"

        # Add exception info if present
        if record.exc_info:
            log_msg += "\n" + self.formatException(record.exc_info)

        return log_msg


def setup_structured_logging(
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    console_output: bool = True,
    json_output: bool = False,
    service_name: str = "digital-calendar",
    environment: str = "production",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
) -> None:
    """
    Configure structured logging for the application

    Args:
        log_dir: Directory for log files
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_output: Whether to output to console
        json_output: Whether to use JSON format (recommended for production)
        service_name: Name of the service for log metadata
        environment: Environment name (development, staging, production)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
    """
    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))

        if json_output:
            console_formatter = JSONFormatter(service_name, environment)
        else:
            console_formatter = ColoredFormatter()

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

    # File handlers
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)

        # Main application log (rotating)
        app_log_file = log_dir / "app.log"
        app_handler = RotatingFileHandler(
            app_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        app_handler.setLevel(logging.INFO)

        if json_output:
            app_formatter = JSONFormatter(service_name, environment)
        else:
            app_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

        app_handler.setFormatter(app_formatter)
        root_logger.addHandler(app_handler)

        # Error log (only errors and critical)
        error_log_file = log_dir / "error.log"
        error_handler = RotatingFileHandler(
            error_log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(
            JSONFormatter(service_name, environment) if json_output
            else logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        root_logger.addHandler(error_handler)

        # Daily rotating log
        daily_log_file = log_dir / "daily.log"
        daily_handler = TimedRotatingFileHandler(
            daily_log_file,
            when='midnight',
            interval=1,
            backupCount=30  # Keep 30 days
        )
        daily_handler.setLevel(logging.INFO)
        daily_handler.setFormatter(
            JSONFormatter(service_name, environment) if json_output
            else logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        root_logger.addHandler(daily_handler)

    # Set specific loggers
    logging.getLogger('werkzeug').setLevel(logging.WARNING)  # Flask request logs
    logging.getLogger('urllib3').setLevel(logging.WARNING)   # HTTP library logs


class StructuredLogger:
    """
    Wrapper for structured logging with extra context

    Example:
        logger = StructuredLogger(__name__)
        logger.info("User logged in", user_id="123", ip="192.168.1.1")
    """

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def _log(self, level: int, message: str, **kwargs: Any) -> None:
        """Log message with extra context"""
        extra = {k: v for k, v in kwargs.items()}
        self.logger.log(level, message, extra=extra)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message"""
        self._log(logging.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message"""
        self._log(logging.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message"""
        self._log(logging.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message"""
        self._log(logging.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message"""
        self._log(logging.CRITICAL, message, **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback"""
        self.logger.exception(message, extra=kwargs)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance

    Args:
        name: Logger name (usually __name__)

    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)
