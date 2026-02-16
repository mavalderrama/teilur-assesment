"""Structured logging configuration for AWS CloudWatch."""
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any


class CloudWatchJSONFormatter(logging.Formatter):
    """JSON formatter optimized for AWS CloudWatch Logs."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for CloudWatch."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields from record
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        # Add correlation ID if present
        if hasattr(record, "correlation_id"):
            log_data["correlation_id"] = record.correlation_id

        return json.dumps(log_data)


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Only configure if not already configured
    if not logger.handlers:
        # Get log level from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Create handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logger.level)

        # Use JSON formatter for production, simple formatter for local dev
        environment = os.getenv("ENVIRONMENT", "production")
        if environment == "production":
            handler.setFormatter(CloudWatchJSONFormatter())
        else:
            # Simple format for local development
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)

        logger.addHandler(handler)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


class LoggerAdapter(logging.LoggerAdapter):
    """Logger adapter with support for extra fields."""

    def process(
        self, msg: str, kwargs: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        """Add extra fields to log record."""
        extra = kwargs.get("extra", {})
        if self.extra:
            extra.update(self.extra)
        kwargs["extra"] = {"extra_fields": extra}
        return msg, kwargs


def get_logger_with_context(name: str, **context: Any) -> LoggerAdapter:
    """
    Get a logger with context fields that will be included in every log.

    Args:
        name: Logger name
        **context: Context fields to include in all logs

    Returns:
        Logger adapter with context
    """
    logger = get_logger(name)
    return LoggerAdapter(logger, context)
