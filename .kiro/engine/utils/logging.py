"""
Logging utilities for the Agent Hooks Enhancement system.
"""

import logging
import sys
from typing import Any, Dict, Optional


class ExecutionError(Exception):
    """Exception raised during hook execution."""
    
    def __init__(self, message: str, hook_id: Optional[str] = None, **kwargs):
        super().__init__(message)
        self.hook_id = hook_id
        self.context = kwargs


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for the given name.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # Configure logger if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    
    return logger