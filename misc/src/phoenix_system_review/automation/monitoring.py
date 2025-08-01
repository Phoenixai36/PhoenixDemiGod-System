"""
Continuous Monitoring for Phoenix Hydra System Review

Provides continuous monitoring capabilities with alerting, health checks,
and automated response to system state changes.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json
from dataclasses import dataclass
from enum import Enum

from ..core.system_controller import SystemController
from ..models.data_models import ComponentCategory, Priority


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """System alert definition"""
    id: str
    level: AlertLevel
    component: str
    message: str
    timestamp: datetime
    metadata: Dict[str, Any] = None
    resolved: bool = False

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class HealthCheck:
    """Health check configuration"""
    name: str
    check_function: Callable
    interval_seconds: int
    timeout_seconds: int = 30
    failure_threshold: int = 3
    enabled: bool = True
    last_run: Optional[datetime] = None
    consecutive_failures: int = 0


class ContinuousMonitoring:
    """
    Continuous monitoring system for Phoenix Hydra

    Features:
    - Health checks for all components
    - Automated alerting and notifications
    - Performance monitoring
    - Trend analysis and reporting
    - Integration with Prometheus metrics
    """

    def __init__(self, controller: SystemController = None, config_path: Path = None):
            self.controller = controller or SystemController()
            self.config_path = config_path or Path.cwd() / ".phoenix_monitoring"
        self.config_path.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.running = False
        self.monitoring_tasks: Dict[str, asyncio.Task] = {}

        # Monitoring state
        self.alerts: List[Alert] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        self.metrics_history: Dict[str, List[Dict[str, Any]]] = {}

        # Load configuration
        self.config = self._load_monitoring_config()
        self._setup_health_checks()

    def _load_monitoring_config(self) -> Dict[str, Any]:
        """Load monitoring configuration"""
        config_file = self.config_path / "monitoring.json"

        default_config = {
            "health_checks": {
                "system_review": {
                    "enabled": True,
                    "interval_seconds": 300,  # 5 minutes
                    "timeout_seconds": 60,
                    "failure_threshold": 2
                },
                "component_health": {
                    "enabled": True,
                    "interval_seconds": 120,  # 2 minutes
                    "timeout_seconds": 30,
                    "failure_threshold": 3
                },
                "service_endpoints": {
                    "enabled": True,
                    "interval_seconds": 60,   # 1 minute
                    "timeout_seconds": 10,
                    "failure_threshold": 3
                },
                "mamba_performance": {
                    "enabled": True,
                    "interval_seconds": 600,  # 10 minutes
                    "timeout_seconds": 120,
                    "failure_threshold": 2
                }
            },
            "alerting": {
                "enabled": True,
                "webhook_urls": [],
                "email_notifications": False,
                "alert_cooldown_minutes": 15
            },
            "metrics": {
                "retention_days": 30,
                "collection_interval_seconds": 60,
                "prometheus_enabled": True,
                "prometheus_url": "http://localhost:9090"
            },
            "thresholds": {
                "completion_percentage_warning": 85.0,
                "completion_percentage_critical": 75.0,
                "response_time_warning_ms": 5000,
                "response_time_critical_ms": 10000,
                "error_rate_warning_percent": 5.0,
                "error_rate_critical_percent": 10.0
            }
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
            except Exception as e:
                self.logger.warning(f"Failed to load monitoring config: {e}")

        return default_config

    def _setup_health_checks(self):
        """Set up health check configurations"""
        health_config = self.config["health_checks"]

        # System review health check
        if health_config["system_review"]["enabled"]:
            self.health_checks["system_review"] = HealthCheck(
                name="system_review",
                check_function=self._check_system_review_health,
                **health_config["system_review"]
            )

        # Component health check
        if health_config["component_health"]["enabled"]:
            self.health_checks["component_health"] = HealthCheck(
                name="component_health",
                check_function=self._check_component_health,
                **health_config["component_health"]
            )

        # Service endpoints check
        if health_config["service_endpoints"]["enabled"]:
            self.health_checks["service_endpoints"] = HealthCheck(
                name="service_endpoints",
                check_function=self._check_service_endpoints,
                **health_config["service_endpoints"]
            )

        # Mamba performance check
        if health_config["mamba_performance"]["enabled"]:
            self.health_checks["mamba_performance"] = HealthCheck(
                name="mamba_performance",
                check_function=self._check_mamba_performance,
                **health_config["mamba_performance"]
            )

    async def start(self):
        """Start continuous monitoring"""
        if self.running:
            self.logger.warning("Monitoring is already running")
            return

        self.running = True
        self.logger.info("Starting Phoenix continuous monitoring...")

        # Start health check tasks
        for name, health_check in self.health_checks.items():
            if health_check.enabled:
                task = asyncio.create_task(
                    self._health_check_loop(health_check)
                )
                self.monitoring_tasks[f"health_{name}"] = task

        # Start metrics collection
        if self.config["metrics"]["prometheus_enabled"]:
            metrics_task = asyncio.create_task(self._metrics_collection_loop())
            self.monitoring_tasks["metrics"] = metrics_task

        # Start alert processing
        alert_task = asyncio.create_task(self._alert_processing_loop())
        self.monitoring_tasks["alerts"] = alert_task

        self.logger.info(
            f"Started {len(self.monitoring_tasks)} monitoring tasks")

    async def stop(self):
        """Stop continuous monitoring"""
        if not self.running:
            return

        self.running = False
        self.logger.info("Stopping Phoenix continuous monitoring...")

        # Cancel all monitoring tasks
        for name, task in self.monitoring_tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self.monitoring_tasks.clear()
        self.logger.info("Phoenix monitoring stopped")

    async def _health_check_loop(self, health_check: HealthCheck):
        """Execute health check loop"""
        while self.running:
            try:
                start_time = datetime.now()

                # Execute health check
                try:
                    result = await asyncio.wait_for(
                        health_check.check_function(),
                        timeout=health_check.timeout_seconds
                    )

                    # Health check passed
                    if health_check.consecutive_failures > 0:
                        # Recovery from previous failures
                        await self._create_alert(
                            level=AlertLevel.INFO,
                            component=health_check.name,
                            message=f"Health check recovered after {health_check.consecutive_failures} failures",
                            metadata={"recovery": True}
                        )

                    health_check.consecutive_failures = 0
                    health_check.last_run = start_time

                except asyncio.TimeoutError:
                    # Health check timeout
                    health_check.consecutive_failures += 1

                    if health_check.consecutive_failures >= health_check.failure_threshold:
                        await self._create_alert(
                            level=AlertLevel.ERROR,
                            component=health_check.name,
                            message=f"Health check timeout after {health_check.timeout_seconds}s",
                            metadata={
                                "consecutive_failures": health_check.consecutive_failures}
                        )

                except Exception as e:
                    # Health check error
                    health_check.consecutive_failures += 1

                    if health_check.consecutive_failures >= health_check.failure_threshold:
                        await self._create_alert(
                            level=AlertLevel.ERROR,
                            component=health_check.name,
                            message=f"Health check failed: {str(e)}",
                            metadata={
                                "error": str(e),
                                "consecutive_failures": health_check.consecutive_failures
                            }
                        )

                # Wait for next check
                await asyncio.sleep(health_check.interval_seconds)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(
                    f"Health check loop error for {health_check.name}: {e}")
                await asyncio.sleep(60)

    async def _check_system_review_health(self) -> Dict[str, Any]:
        """Check overall system review health"""
        try:
            # Quick system status check
            status = await self.controller.get_system_status(
                include_services=False,
                components=None
            )

            # Calculate overall health score
            total_components = 0
            healthy_components = 0

            for category, components in status.get('components', {}).items():
                for component, comp_status in components.items():
                    total_components += 1
                    if comp_status.get('healthy', False):
                        healthy_components += 1

            health_percentage = (
                healthy_components / total_components * 100) if total_components > 0 else 0

            # Check against thresholds
            thresholds = self.config["thresholds"]
            if health_percentage < thresholds["completion_percentage_critical"]:
                raise Exception(
                    f"System health critical: {health_percentage:.1f}%")
            elif health_percentage < thresholds["completion_percentage_warning"]:
                await self._create_alert(
                    level=AlertLevel.WARNING,
                    component="system_review",
                    message=f"System health warning: {health_percentage:.1f}%",
                    metadata={"health_percentage": health_percentage}
                )

            return {
                "healthy": True,
                "health_percentage": health_percentage,
                "total_components": total_components,
                "healthy_components": healthy_components
            }

        except Exception as e:
            raise Exception(f"System review health check failed: {e}")

    async def _check_component_health(self) -> Dict[str, Any]:
        """Check individual component health"""
        try:
            # This would perform detailed component analysis
            # For now, return a simplified check
            return {"healthy": True, "components_checked": 0}

        except Exception as e:
            raise Exception(f"Component health check failed: {e}")

    async def _check_service_endpoints(self) -> Dict[str, Any]:
        """Check service endpoint health"""
        try:
            service_status = await self.controller.get_system_status(
                include_services=True,
                components=None
            )

            services = service_status.get('services', {})
            unhealthy_services = [
                name for name, status in services.items()
                if not status.get('healthy', False)
            ]

            if unhealthy_services:
                raise Exception(
                    f"Unhealthy services: {', '.join(unhealthy_services)}")

            return {
                "healthy": True,
                "services_checked": len(services),
                "all_healthy": len(unhealthy_services) == 0
            }

        except Exception as e:
            raise Exception(f"Service endpoint check failed: {e}")

    async def _check_mamba_performance(self) -> Dict[str, Any]:
        """Check Mamba/SSM performance metrics"""
        try:
            # This would check Mamba model performance
            # Integration with metrics.py for energy consumption, latency, etc.

            # Placeholder implementation
            return {
                "healthy": True,
                "energy_efficiency": "optimal",
                "latency_ms": 1500,
                "throughput": "normal"
            }

        except Exception as e:
            raise Exception(f"Mamba performance check failed: {e}")

    async def _metrics_collection_loop(self):
        """Collect and store metrics"""
        while self.running:
            try:
                timestamp = datetime.now()

                # Collect system metrics
                metrics = await self._collect_system_metrics()

                # Store metrics
                for metric_name, value in metrics.items():
                    if metric_name not in self.metrics_history:
                        self.metrics_history[metric_name] = []

                    self.metrics_history[metric_name].append({
                        "timestamp": timestamp.isoformat(),
                        "value": value
                    })

                    # Cleanup old metrics
                    retention_days = self.config["metrics"]["retention_days"]
                    cutoff_date = timestamp - timedelta(days=retention_days)

                    self.metrics_history[metric_name] = [
                        entry for entry in self.metrics_history[metric_name]
                        if datetime.fromisoformat(entry["timestamp"]) > cutoff_date
                    ]

                # Save metrics to disk
                await self._save_metrics()

                # Wait for next collection
                interval = self.config["metrics"]["collection_interval_seconds"]
                await asyncio.sleep(interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(60)

    async def _collect_system_metrics(self) -> Dict[str, Any]:
        """Collect current system metrics"""
        try:
            status = await self.controller.get_system_status()

            # Calculate metrics
            total_components = sum(
                len(components) for components in status.get('components', {}).values()
            )

            healthy_components = sum(
                sum(1 for comp_status in components.values()
                    if comp_status.get('healthy', False))
                for components in status.get('components', {}).values()
            )

            health_percentage = (
                healthy_components / total_components * 100) if total_components > 0 else 0

            return {
                "system_health_percentage": health_percentage,
                "total_components": total_components,
                "healthy_components": healthy_components,
                "active_alerts": len([a for a in self.alerts if not a.resolved])
            }

        except Exception as e:
            self.logger.error(f"Failed to collect metrics: {e}")
            return {}

    async def _save_metrics(self):
        """Save metrics to disk"""
        try:
            metrics_file = self.config_path / "metrics_history.json"

            with open(metrics_file, 'w') as f:
                json.dump(self.metrics_history, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save metrics: {e}")

    async def _alert_processing_loop(self):
        """Process and send alerts"""
        while self.running:
            try:
                # Process pending alerts
                unprocessed_alerts = [a for a in self.alerts if not a.resolved]

                for alert in unprocessed_alerts:
                    await self._process_alert(alert)

                await asyncio.sleep(30)  # Check every 30 seconds

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Alert processing error: {e}")
                await asyncio.sleep(60)

    async def _create_alert(
        self,
        level: AlertLevel,
        component: str,
        message: str,
        metadata: Dict[str, Any] = None
    ):
        """Create a new alert"""
        alert = Alert(
            id=f"{component}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            level=level,
            component=component,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )

        self.alerts.append(alert)
        self.logger.warning(
            f"Alert created: {level.value.upper()} - {component}: {message}")

    async def _process_alert(self, alert: Alert):
        """Process and send alert notifications"""
        try:
            # Check cooldown
            cooldown_minutes = self.config["alerting"]["alert_cooldown_minutes"]
            cutoff_time = datetime.now() - timedelta(minutes=cooldown_minutes)

            # Check if similar alert was sent recently
            recent_similar = [
                a for a in self.alerts
                if (a.component == alert.component and
                    a.level == alert.level and
                    a.timestamp > cutoff_time and
                    a.resolved)
            ]

            if recent_similar:
                return  # Skip due to cooldown

            # Send webhook notifications
            if self.config["alerting"]["enabled"]:
                await self._send_webhook_alerts(alert)

            # Mark as processed
            alert.resolved = True

        except Exception as e:
            self.logger.error(f"Failed to process alert {alert.id}: {e}")

    async def _send_webhook_alerts(self, alert: Alert):
        """Send alert via webhooks"""
        webhook_urls = self.config["alerting"]["webhook_urls"]

        if not webhook_urls:
            return

        alert_data = {
            "id": alert.id,
            "level": alert.level.value,
            "component": alert.component,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metadata": alert.metadata
        }

        import aiohttp

        for webhook_url in webhook_urls:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url,
                        json=alert_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            self.logger.info(
                                f"Alert sent to webhook: {webhook_url}")
                        else:
                            self.logger.warning(
                                f"Webhook failed: {response.status}")

            except Exception as e:
                self.logger.error(
                    f"Failed to send webhook to {webhook_url}: {e}")

    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        return {
            "running": self.running,
            "active_tasks": list(self.monitoring_tasks.keys()),
            "health_checks": {
                name: {
                    "enabled": hc.enabled,
                    "last_run": hc.last_run.isoformat() if hc.last_run else None,
                    "consecutive_failures": hc.consecutive_failures
                }
                for name, hc in self.health_checks.items()
            },
            "active_alerts": len([a for a in self.alerts if not a.resolved]),
            "total_alerts": len(self.alerts),
            "metrics_collected": len(self.metrics_history)
        }
