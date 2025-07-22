"""
Logging utilities for the Phoenix DemiGod system.

This module provides standardized logging setup and access for all components.
"""

import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from typing import Dict, Optional

import structlog


# Global configuration
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_LOG_FILE = "logs/phoenix_demigod.log"
DEFAULT_MAX_BYTES = 10 * 1024 * 1024  # 10 MB
DEFAULT_BACKUP_COUNT = 5

# Store loggers to avoid creating duplicates
_loggers: Dict[str, logging.Logger] = {}


def setup_logging(
    log_level: Optional[str] = None,
    log_format: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: Optional[int] = None,
    backup_count: Optional[int] = None,
    use_structlog: bool = True
) -> None:
    """
    Set up logging for the Phoenix DemiGod system.
    
    Args:
        log_level: Logging level (default: INFO)
        log_format: Log message format (default: timestamp - name - level - message)
        log_file: Path to log file (default: logs/phoenix_demigod.log)
        max_bytes: Maximum log file size before rotation (default: 10 MB)
        backup_count: Number of backup log files to keep (default: 5)
        use_structlog: Whether to use structured logging (default: True)
    """
    # Convert log level string to constant
    level_name = log_level or os.environ.get("PHOENIX_LOG_LEVEL", "INFO")
    level = getattr(logging, level_name.upper(), DEFAULT_LOG_LEVEL)
    
    # Get other parameters from environment or defaults
    log_format = log_format or os.environ.get("PHOENIX_LOG_FORMAT", DEFAULT_LOG_FORMAT)
    log_file = log_file or os.environ.get("PHOENIX_LOG_FILE", DEFAULT_LOG_FILE)
    max_bytes = max_bytes or int(os.environ.get("PHOENIX_LOG_MAX_BYTES", DEFAULT_MAX_BYTES))
    backup_count = backup_count or int(os.environ.get("PHOENIX_LOG_BACKUP_COUNT", DEFAULT_BACKUP_COUNT))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_formatter = logging.Formatter(log_format)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # Create file handler if log file is specified
    if log_file:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        file_handler.setLevel(level)
        file_formatter = logging.Formatter(log_format)
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Configure structlog if requested
    if use_structlog:
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
    
    # Log startup message
    root_logger.info(f"Phoenix DemiGod logging initialized at level {level_name}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    
    Args:
        name: Logger name (typically module name)
        
    Returns:
        Logger instance
    """
    if name not in _loggers:
        _loggers[name] = logging.getLogger(name)
    return _loggers[name]


# Initialize logging with default settings
setup_logging()


if __name__ == "__main__":
    # Example usage
    logger = get_logger("phoenix_demigod.example")
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    try:
        raise ValueError("Example exception")
    except Exception as e:
        logger.exception("This is an exception message")