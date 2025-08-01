"""
Custom exception types for the Phoenix Hydra System Review tool.
"""

from typing import Optional


class PhoenixSystemError(Exception):
    """Base exception class for all application-specific errors."""

    def __init__(self, message: str, original_exception: Optional[Exception] = None):
        super().__init__(message)
        self.original_exception = original_exception


class DiscoveryError(PhoenixSystemError):
    """Exception raised for errors during the discovery phase."""


class AnalysisError(PhoenixSystemError):
    """Exception raised for errors during the analysis phase."""


class AssessmentError(PhoenixSystemError):
    """Exception raised for errors during the assessment phase."""


class ConfigurationError(PhoenixSystemError):
    """Exception raised for configuration-related errors."""
