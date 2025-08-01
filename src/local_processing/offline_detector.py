"""
Offline Capability Detection and Fallback System

This module provides intelligent detection of offline/online status and
implements robust fallback mechanisms for local AI processing.
"""

import asyncio
import json
import logging
import socket
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class ConnectivityStatus(Enum):
    """Network connectivity status."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"
    UNKNOWN = "unknown"


class FallbackStrategy(Enum):
    """Fallback strategy options."""

    SMALLER_MODEL = "smaller_model"
    CACHED_RESULTS = "cached_results"
    SIMPLIFIED_PROCESSING = "simplified_processing"
    GRACEFUL_DEGRADATION = "graceful_degradation"


@dataclass
class ConnectivityCheck:
    """Configuration for a connectivity check."""

    name: str
    host: str
    port: int
    timeout: float
    weight: float  # Importance weight (0.0 to 1.0)


@dataclass
class FallbackConfig:
    """Configuration for fallback behavior."""

    strategy: FallbackStrategy
    trigger_conditions: Dict[str, Any]
    fallback_model: Optional[str]
    performance_threshold: float
    max_retries: int


class OfflineDetector:
    """
    Detects network connectivity status and manages offline/online transitions.

    Uses multiple connectivity checks with weighted scoring to determine
    the overall connectivity status and trigger appropriate fallbacks.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.connectivity_checks: List[ConnectivityCheck] = []
        self.current_status = ConnectivityStatus.UNKNOWN
        self.last_check_time = 0.0
        self.check_interval = 30.0  # seconds
        self.status_callbacks: List[Callable] = []
        self.connectivity_history: List[tuple] = []  # (timestamp, status)

        # Load configuration
        if config_path and config_path.exists():
            self._load_config(config_path)
        else:
            self._setup_default_checks()

    def _setup_default_checks(self):
        """Setup default connectivity checks."""
        self.connectivity_checks = [
            ConnectivityCheck("google_dns", "8.8.8.8", 53, 3.0, 0.3),
            ConnectivityCheck("cloudflare_dns", "1.1.1.1", 53, 3.0, 0.3),
            ConnectivityCheck("github", "github.com", 443, 5.0, 0.2),
            ConnectivityCheck("pypi", "pypi.org", 443, 5.0, 0.2),
        ]

    def _load_config(self, config_path: Path):
        """Load connectivity check configuration from file."""
        try:
            with open(config_path) as f:
                config = json.load(f)

            self.connectivity_checks = [
                ConnectivityCheck(**check) for check in config.get("checks", [])
            ]
            self.check_interval = config.get("check_interval", 30.0)

        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            self._setup_default_checks()

    async def start_monitoring(self):
        """Start continuous connectivity monitoring."""
        logger.info("Starting connectivity monitoring")

        while True:
            try:
                await self._perform_connectivity_check()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in connectivity monitoring: {e}")
                await asyncio.sleep(5.0)  # Short retry delay

    async def _perform_connectivity_check(self) -> ConnectivityStatus:
        """Perform connectivity check using all configured endpoints."""
        check_results = []

        # Run all checks concurrently
        tasks = [self._check_endpoint(check) for check in self.connectivity_checks]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Calculate weighted score
        total_weight = 0.0
        success_weight = 0.0

        for i, result in enumerate(results):
            check = self.connectivity_checks[i]
            total_weight += check.weight

            if isinstance(result, bool) and result:
                success_weight += check.weight
                check_results.append((check.name, True))
            else:
                check_results.append((check.name, False))

        # Determine status based on weighted success rate
        if total_weight == 0:
            new_status = ConnectivityStatus.UNKNOWN
        else:
            success_rate = success_weight / total_weight
            if success_rate >= 0.8:
                new_status = ConnectivityStatus.ONLINE
            elif success_rate >= 0.3:
                new_status = ConnectivityStatus.DEGRADED
            else:
                new_status = ConnectivityStatus.OFFLINE

        # Update status and notify callbacks if changed
        if new_status != self.current_status:
            old_status = self.current_status
            self.current_status = new_status
            self.last_check_time = time.time()

            # Add to history
            self.connectivity_history.append((self.last_check_time, new_status))

            # Keep only last 100 entries
            if len(self.connectivity_history) > 100:
                self.connectivity_history = self.connectivity_history[-100:]

            logger.info(
                f"Connectivity status changed: {old_status.value} -> {new_status.value}"
            )

            # Notify callbacks
            for callback in self.status_callbacks:
                try:
                    await callback(old_status, new_status, check_results)
                except Exception as e:
                    logger.error(f"Error in status callback: {e}")

        return new_status

    async def _check_endpoint(self, check: ConnectivityCheck) -> bool:
        """Check connectivity to a specific endpoint."""
        try:
            # Create socket connection
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(check.timeout)

            result = sock.connect_ex((check.host, check.port))
            sock.close()

            success = result == 0
            logger.debug(
                f"Connectivity check {check.name}: {'SUCCESS' if success else 'FAILED'}"
            )
            return success

        except Exception as e:
            logger.debug(f"Connectivity check {check.name} failed: {e}")
            return False

    def add_status_callback(self, callback: Callable):
        """Add a callback to be notified of status changes."""
        self.status_callbacks.append(callback)

    def get_current_status(self) -> ConnectivityStatus:
        """Get the current connectivity status."""
        return self.current_status

    def is_offline(self) -> bool:
        """Check if currently offline."""
        return self.current_status == ConnectivityStatus.OFFLINE

    def is_online(self) -> bool:
        """Check if currently online."""
        return self.current_status == ConnectivityStatus.ONLINE

    def get_connectivity_history(self) -> List[tuple]:
        """Get recent connectivity history."""
        return self.connectivity_history.copy()


class FallbackManager:
    """
    Manages fallback strategies when offline or when primary models fail.

    Implements intelligent fallback logic based on system resources,
    model availability, and performance requirements.
    """

    def __init__(self, model_manager):
        self.model_manager = model_manager
        self.fallback_configs: Dict[str, FallbackConfig] = {}
        self.active_fallbacks: Dict[str, Any] = {}
        self.performance_cache: Dict[str, float] = {}

        self._setup_default_fallbacks()

    def _setup_default_fallbacks(self):
        """Setup default fallback configurations."""
        self.fallback_configs = {
            "memory_constrained": FallbackConfig(
                strategy=FallbackStrategy.SMALLER_MODEL,
                trigger_conditions={"max_memory_mb": 2048},
                fallback_model="phoenix-ssm-lite",
                performance_threshold=0.7,
                max_retries=3,
            ),
            "offline_mode": FallbackConfig(
                strategy=FallbackStrategy.CACHED_RESULTS,
                trigger_conditions={"connectivity": "offline"},
                fallback_model=None,
                performance_threshold=0.5,
                max_retries=1,
            ),
            "model_corruption": FallbackConfig(
                strategy=FallbackStrategy.SMALLER_MODEL,
                trigger_conditions={"model_status": "corrupted"},
                fallback_model="phoenix-ssm-backup",
                performance_threshold=0.6,
                max_retries=2,
            ),
        }

    async def handle_fallback(
        self, scenario: str, context: Dict[str, Any]
    ) -> Optional[Any]:
        """
        Handle a fallback scenario.

        Args:
            scenario: Fallback scenario name
            context: Context information for the fallback

        Returns:
            Fallback result or None if no fallback available
        """
        if scenario not in self.fallback_configs:
            logger.warning(f"No fallback config for scenario: {scenario}")
            return None

        config = self.fallback_configs[scenario]

        try:
            if config.strategy == FallbackStrategy.SMALLER_MODEL:
                return await self._fallback_to_smaller_model(config, context)
            elif config.strategy == FallbackStrategy.CACHED_RESULTS:
                return await self._fallback_to_cached_results(config, context)
            elif config.strategy == FallbackStrategy.SIMPLIFIED_PROCESSING:
                return await self._fallback_to_simplified_processing(config, context)
            elif config.strategy == FallbackStrategy.GRACEFUL_DEGRADATION:
                return await self._fallback_graceful_degradation(config, context)
            else:
                logger.error(f"Unknown fallback strategy: {config.strategy}")
                return None

        except Exception as e:
            logger.error(f"Fallback handling failed for {scenario}: {e}")
            return None

    async def _fallback_to_smaller_model(
        self, config: FallbackConfig, context: Dict[str, Any]
    ) -> Optional[Any]:
        """Fallback to a smaller, more efficient model."""
        if not config.fallback_model:
            # Find the smallest available model of the same type
            original_model_type = context.get("model_type", "mamba")
            fallback_metadata = self.model_manager.get_fallback_model(
                original_model_type
            )

            if not fallback_metadata:
                logger.error(
                    f"No fallback model available for type: {original_model_type}"
                )
                return None

            fallback_model_name = fallback_metadata.name
        else:
            fallback_model_name = config.fallback_model

        logger.info(f"Falling back to smaller model: {fallback_model_name}")

        # Load the fallback model
        fallback_model = await self.model_manager.load_model(fallback_model_name)
        if fallback_model:
            self.active_fallbacks[context.get("request_id", "default")] = {
                "model": fallback_model,
                "strategy": config.strategy,
                "performance_degradation": 1.0 - config.performance_threshold,
            }
            return fallback_model

        return None

    async def _fallback_to_cached_results(
        self, config: FallbackConfig, context: Dict[str, Any]
    ) -> Optional[Any]:
        """Fallback to cached results from previous computations."""
        cache_key = context.get("cache_key")
        if not cache_key:
            return None

        # This would integrate with a caching system
        # For now, return a placeholder
        logger.info(f"Attempting to use cached results for: {cache_key}")

        # Simulate cache lookup
        cached_result = self.performance_cache.get(cache_key)
        if cached_result:
            logger.info(f"Using cached result for {cache_key}")
            return {"cached": True, "result": cached_result}

        return None

    async def _fallback_to_simplified_processing(
        self, config: FallbackConfig, context: Dict[str, Any]
    ) -> Optional[Any]:
        """Fallback to simplified processing logic."""
        logger.info("Falling back to simplified processing")

        # Implement simplified processing logic
        # This would be task-specific
        return {
            "simplified": True,
            "performance_threshold": config.performance_threshold,
            "processing_mode": "basic",
        }

    async def _fallback_graceful_degradation(
        self, config: FallbackConfig, context: Dict[str, Any]
    ) -> Optional[Any]:
        """Implement graceful degradation of functionality."""
        logger.info("Implementing graceful degradation")

        return {
            "degraded": True,
            "available_features": ["basic_analysis", "simple_reporting"],
            "disabled_features": ["advanced_analysis", "real_time_processing"],
        }

    def register_fallback_config(self, name: str, config: FallbackConfig):
        """Register a new fallback configuration."""
        self.fallback_configs[name] = config
        logger.info(f"Registered fallback config: {name}")

    def get_active_fallbacks(self) -> Dict[str, Any]:
        """Get currently active fallbacks."""
        return self.active_fallbacks.copy()

    def clear_fallback(self, request_id: str):
        """Clear an active fallback."""
        if request_id in self.active_fallbacks:
            del self.active_fallbacks[request_id]
            logger.info(f"Cleared fallback for request: {request_id}")


class LocalProcessingOrchestrator:
    """
    Orchestrates local AI processing with offline detection and fallback management.

    This is the main coordinator that brings together model management,
    offline detection, and fallback strategies.
    """

    def __init__(self, models_dir: Path = Path("models")):
        self.model_manager = LocalModelManager(models_dir)
        self.offline_detector = OfflineDetector()
        self.fallback_manager = FallbackManager(self.model_manager)

        # Register for connectivity status changes
        self.offline_detector.add_status_callback(self._on_connectivity_change)

    async def start(self):
        """Start the local processing orchestrator."""
        logger.info("Starting Local Processing Orchestrator")

        # Start connectivity monitoring
        asyncio.create_task(self.offline_detector.start_monitoring())

        # Perform initial connectivity check
        await self.offline_detector._perform_connectivity_check()

        logger.info("Local Processing Orchestrator started successfully")

    async def process_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process an AI request with automatic fallback handling.

        Args:
            request: Processing request with model requirements

        Returns:
            Processing result with metadata about fallbacks used
        """
        request_id = request.get("id", f"req_{int(time.time())}")
        model_name = request.get("model", "phoenix-ssm-default")

        try:
            # Try to load the requested model
            model = await self.model_manager.load_model(model_name)

            if model:
                # Process with primary model
                result = await self._process_with_model(model, request)
                return {
                    "success": True,
                    "result": result,
                    "model_used": model_name,
                    "fallback_used": False,
                    "connectivity_status": self.offline_detector.get_current_status().value,
                }
            else:
                # Primary model failed, try fallback
                logger.warning(
                    f"Primary model {model_name} unavailable, trying fallback"
                )

                fallback_result = await self.fallback_manager.handle_fallback(
                    "model_corruption",
                    {
                        "request_id": request_id,
                        "model_type": request.get("model_type", "mamba"),
                        "original_model": model_name,
                    },
                )

                if fallback_result:
                    result = await self._process_with_model(fallback_result, request)
                    return {
                        "success": True,
                        "result": result,
                        "model_used": "fallback",
                        "fallback_used": True,
                        "connectivity_status": self.offline_detector.get_current_status().value,
                    }
                else:
                    return {
                        "success": False,
                        "error": "No model or fallback available",
                        "connectivity_status": self.offline_detector.get_current_status().value,
                    }

        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "connectivity_status": self.offline_detector.get_current_status().value,
            }

    async def _process_with_model(self, model: Any, request: Dict[str, Any]) -> Any:
        """
        Process a request with a specific model.
        This would be implemented based on the actual model interface.
        """
        # Placeholder for actual model processing
        await asyncio.sleep(0.1)  # Simulate processing time

        return {
            "processed": True,
            "input": request.get("input", ""),
            "model_info": str(model),
        }

    async def _on_connectivity_change(
        self,
        old_status: ConnectivityStatus,
        new_status: ConnectivityStatus,
        check_results: List[tuple],
    ):
        """Handle connectivity status changes."""
        logger.info(f"Connectivity changed: {old_status.value} -> {new_status.value}")

        if new_status == ConnectivityStatus.OFFLINE:
            # Switch to offline mode
            logger.info("Switching to offline mode")
            # Could trigger model preloading, cache warming, etc.

        elif old_status == ConnectivityStatus.OFFLINE and new_status in [
            ConnectivityStatus.ONLINE,
            ConnectivityStatus.DEGRADED,
        ]:
            # Coming back online
            logger.info("Coming back online")
            # Could trigger model updates, cache synchronization, etc.

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "connectivity": self.offline_detector.get_current_status().value,
            "loaded_models": len(self.model_manager._active_models),
            "active_fallbacks": len(self.fallback_manager.get_active_fallbacks()),
            "total_models": len(self.model_manager.list_models()),
            "last_connectivity_check": self.offline_detector.last_check_time,
        }
