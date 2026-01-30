"""
Structured Logging Configuration.

This module sets up JSON-formatted logging for production readiness.
Every log includes context like request_id, user, timestamp, etc.

Why Structured Logging?
- Machine-readable (easy to parse with tools like ELK, Splunk)
- Consistent format across all logs
- Request tracing with unique IDs
- Easy filtering and aggregation
"""

import logging
import sys
import uuid
from datetime import datetime
from typing import Any, Dict
from pythonjsonlogger import jsonlogger

from app.core.settings import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON log formatter that adds extra context to every log.
    
    Adds:
    - timestamp (ISO 8601)
    - app_name
    - environment
    - log_level
    """
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to every log record."""
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp in ISO 8601 format
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"
        
        # Add application context
        log_record["app_name"] = settings.app_name
        log_record["environment"] = settings.environment
        log_record["level"] = record.levelname
        
        # Add source code location
        log_record["module"] = record.module
        log_record["function"] = record.funcName
        log_record["line"] = record.lineno


def setup_logging() -> logging.Logger:
    """
    Configure and return the application logger.
    
    Logs are written to:
    - stdout (console) - Always
    - logs/app.log (file) - Only if logs/ directory exists
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(settings.app_name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Console handler (stdout) - JSON format
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    
    # JSON formatter
    json_formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )
    console_handler.setFormatter(json_formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional) - same JSON format
    try:
        file_handler = logging.FileHandler("logs/app.log")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(json_formatter)
        logger.addHandler(file_handler)
    except (FileNotFoundError, PermissionError):
        # If logs directory doesn't exist, skip file logging
        pass
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger() -> logging.Logger:
    """
    Get or create the application logger.
    
    Use this function to get a logger instance in your code:
    
    ```python
    from app.core.logger import get_logger
    
    logger = get_logger()
    logger.info("Processing request", extra={"user_id": 123})
    ```
    
    Returns:
        Logger instance
    """
    logger_name = settings.app_name
    logger = logging.getLogger(logger_name)
    
    # If logger hasn't been set up yet, set it up now
    if not logger.handlers:
        return setup_logging()
    
    return logger


def generate_request_id() -> str:
    """
    Generate a unique request ID for tracing.
    
    Format: req_<uuid4>
    Example: req_a1b2c3d4-e5f6-7890-abcd-ef1234567890
    
    Returns:
        Unique request ID string
    """
    return f"req_{uuid.uuid4()}"


# Module-level logger instance
logger = get_logger()
