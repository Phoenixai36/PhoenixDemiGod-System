"""
Phoenix Hydra System Review Tool

A comprehensive evaluation framework for analyzing Phoenix Hydra system components
and generating prioritized TODO checklists for achieving 100% completion.
"""

__version__ = "1.0.0"
__author__ = "Phoenix Team"

from .core.interfaces import (
    DiscoveryEngine,
    AnalysisEngine,
    AssessmentEngine,
    ReportingEngine
)

from .models.data_models import (
    Component,
    EvaluationResult,
    Gap,
    TODOTask,
    ComponentCategory,
    Priority,
    TaskStatus
)

__all__ = [
    "DiscoveryEngine",
    "AnalysisEngine", 
    "AssessmentEngine",
    "ReportingEngine",
    "Component",
    "EvaluationResult",
    "Gap",
    "TODOTask",
    "ComponentCategory",
    "Priority",
    "TaskStatus"
]