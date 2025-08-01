"""
Review Scheduler for automated Phoenix Hydra system reviews

Provides scheduling capabilities for running system reviews at regular intervals,
with configurable triggers and notification systems.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
import json
from dataclasses import dataclass
from enum import Enum

from ..core.system_controller import SystemReviewController
from ..models.data_models import ComponentCategory


class ScheduleType(Enum):
    """Types of scheduling intervals"""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"


@dataclass
class ScheduledReview:
    """Configuration for a scheduled review"""
    name: str
    schedule_type: ScheduleType
    interval_minutes: int
    components: Optional[List[ComponentCategory]] = None
    output_format: str = "json"
    enabled: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    notification_webhooks: List[str] = None

    def __post_init__(self):
        if self.notification_webhooks is None:
            self.notification_webhooks = []


class ReviewScheduler:
    """
    Automated scheduler for Phoenix Hydra system reviews

    Features:
    - Multiple scheduling intervals (hourly, daily, weekly, monthly)
    - Component-specific reviews
    - Webhook notifications for results
    - Persistent scheduling state
    - Error handling and retry logic
    """

    def __init__(self, controller: SystemReviewController, config_dir: Path = None):
        self.controller = controller
        self.config_dir = config_dir or Path.cwd() / ".phoenix_scheduler"
        self.config_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.scheduled_reviews: Dict[str, ScheduledReview] = {}
        self.running = False
        self.scheduler_task: Optional[asyncio.Task] = None

        # Load existing schedules
        self._load_schedules()

    def _load_schedules(self):
        """Load scheduled reviews from configuration"""
        schedule_file = self.config_dir / "schedules.json"

        if schedule_file.exists():
            try:
                with open(schedule_file, 'r') as f:
                    data = json.load(f)

                for name, config in data.items():
                    # Convert datetime strings back to datetime objects
                    if config.get('last_run'):
                        config['last_run'] = datetime.fromisoformat(
                            config['last_run'])
                    if config.get('next_run'):
                        config['next_run'] = datetime.fromisoformat(
                            config['next_run'])

                    # Convert component strings to enums
                    if config.get('components'):
                        config['components'] = [
                            ComponentCategory(comp) for comp in config['components']
                        ]

                    self.scheduled_reviews[name] = ScheduledReview(
                        name=name,
                        schedule_type=ScheduleType(config['schedule_type']),
                        **{k: v for k, v in config.items() if k not in ['name', 'schedule_type']}
                    )

                self.logger.info(
                    f"Loaded {len(self.scheduled_reviews)} scheduled reviews")

            except Exception as e:
                self.logger.error(f"Failed to load schedules: {e}")

    def _save_schedules(self):
        """Save scheduled reviews to configuration"""
        schedule_file = self.config_dir / "schedules.json"

        try:
            data = {}
            for name, review in self.scheduled_reviews.items():
                config = {
                    'schedule_type': review.schedule_type.value,
                    'interval_minutes': review.interval_minutes,
                    'output_format': review.output_format,
                    'enabled': review.enabled,
                    'notification_webhooks': review.notification_webhooks
                }

                if review.components:
                    config['components'] = [
                        comp.value for comp in review.components]

                if review.last_run:
                    config['last_run'] = review.last_run.isoformat()

                if review.next_run:
                    config['next_run'] = review.next_run.isoformat()

                data[name] = config

            with open(schedule_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.logger.error(f"Failed to save schedules: {e}")

    def add_schedule(
        self,
        name: str,
        schedule_type: ScheduleType,
        interval_minutes: int = None,
        components: List[ComponentCategory] = None,
        output_format: str = "json",
        notification_webhooks: List[str] = None
    ) -> ScheduledReview:
        """Add a new scheduled review"""

        # Calculate interval based on schedule type if not provided
        if interval_minutes is None:
            interval_map = {
                ScheduleType.HOURLY: 60,
                ScheduleType.DAILY: 24 * 60,
                ScheduleType.WEEKLY: 7 * 24 * 60,
                ScheduleType.MONTHLY: 30 * 24 * 60
            }
            interval_minutes = interval_map.get(schedule_type, 60)

        # Calculate next run time
        next_run = datetime.now() + timedelta(minutes=interval_minutes)

        scheduled_review = ScheduledReview(
            name=name,
            schedule_type=schedule_type,
            interval_minutes=interval_minutes,
            components=components,
            output_format=output_format,
            next_run=next_run,
            notification_webhooks=notification_webhooks or []
        )

        self.scheduled_reviews[name] = scheduled_review
        self._save_schedules()

        self.logger.info(
            f"Added scheduled review '{name}' - next run: {next_run}")
        return scheduled_review

    def remove_schedule(self, name: str) -> bool:
        """Remove a scheduled review"""
        if name in self.scheduled_reviews:
            del self.scheduled_reviews[name]
            self._save_schedules()
            self.logger.info(f"Removed scheduled review '{name}'")
            return True
        return False

    def enable_schedule(self, name: str) -> bool:
        """Enable a scheduled review"""
        if name in self.scheduled_reviews:
            self.scheduled_reviews[name].enabled = True
            self._save_schedules()
            return True
        return False

    def disable_schedule(self, name: str) -> bool:
        """Disable a scheduled review"""
        if name in self.scheduled_reviews:
            self.scheduled_reviews[name].enabled = False
            self._save_schedules()
            return True
        return False

    def list_schedules(self) -> List[ScheduledReview]:
        """List all scheduled reviews"""
        return list(self.scheduled_reviews.values())

    async def start_scheduler(self):
        """Start the scheduler daemon"""
        if self.running:
            self.logger.warning("Scheduler is already running")
            return

        self.running = True
        self.scheduler_task = asyncio.create_task(self._scheduler_loop())
        self.logger.info("Review scheduler started")

    async def stop_scheduler(self):
        """Stop the scheduler daemon"""
        if not self.running:
            return

        self.running = False

        if self.scheduler_task:
            self.scheduler_task.cancel()
            try:
                await self.scheduler_task
            except asyncio.CancelledError:
                pass

        self.logger.info("Review scheduler stopped")

    async def _scheduler_loop(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()

                # Check each scheduled review
                for name, review in self.scheduled_reviews.items():
                    if not review.enabled:
                        continue

                    if review.next_run and current_time >= review.next_run:
                        self.logger.info(f"Executing scheduled review: {name}")

                        try:
                            await self._execute_scheduled_review(review)

                            # Update schedule for next run
                            review.last_run = current_time
                            review.next_run = current_time + \
                                timedelta(minutes=review.interval_minutes)

                        except Exception as e:
                            self.logger.error(
                                f"Scheduled review '{name}' failed: {e}")

                            # Schedule retry in 5 minutes
                            review.next_run = current_time + \
                                timedelta(minutes=5)

                # Save updated schedules
                self._save_schedules()

                # Sleep for 1 minute before next check
                await asyncio.sleep(60)

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Scheduler loop error: {e}")
                await asyncio.sleep(60)

    async def _execute_scheduled_review(self, review: ScheduledReview):
        """Execute a scheduled review"""

        # Configure controller if needed
        project_path = Path.cwd()  # Could be configurable
        config = {
            "project_path": str(project_path),
            "output_directory": f"reports/scheduled/{review.name}",
            "include_patterns": ["*.py", "*.yaml", "*.json", "*.md"],
            "exclude_patterns": ["*.pyc", "__pycache__/*", ".git/*"]
        }

        await self.controller.configure(
            project_path=project_path,
            config=config,
            skip_services=False,
            parallel_tasks=2  # Lower for scheduled runs
        )

        # Execute review phases
        discovery_results = await self.controller.discover_components(
            include_components=review.components
        )

        analysis_results = await self.controller.analyze_components(
            discovery_results
        )

        assessment_results = await self.controller.assess_completion(
            analysis_results
        )

        reports = await self.controller.generate_reports(
            assessment_results,
            output_format=review.output_format
        )

        # Save reports
        output_dir = Path(config["output_directory"])
        output_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        for report_type, content in reports.items():
            filename = f"{review.name}_{report_type}_{timestamp}.{review.output_format}"
            output_file = output_dir / filename

            if review.output_format == 'json':
                with open(output_file, 'w') as f:
                    json.dump(content, f, indent=2, default=str)
            else:
                with open(output_file, 'w') as f:
                    f.write(content)

        # Send notifications
        if review.notification_webhooks:
            await self._send_notifications(review, assessment_results, reports)

        self.logger.info(
            f"Scheduled review '{review.name}' completed successfully")

    async def _send_notifications(
        self,
        review: ScheduledReview,
        assessment_results: Dict[str, Any],
        reports: Dict[str, Any]
    ):
        """Send webhook notifications for completed review"""

        notification_data = {
            "review_name": review.name,
            "timestamp": datetime.now().isoformat(),
            "completion_percentage": assessment_results.get('overall_completion', 0),
            "gaps_identified": len(assessment_results.get('gaps', [])),
            "status": "completed"
        }

        import aiohttp

        for webhook_url in review.notification_webhooks:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.post(
                        webhook_url,
                        json=notification_data,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 200:
                            self.logger.info(
                                f"Notification sent to {webhook_url}")
                        else:
                            self.logger.warning(
                                f"Notification failed: {response.status}")

            except Exception as e:
                self.logger.error(
                    f"Failed to send notification to {webhook_url}: {e}")

    async def run_schedule_now(self, name: str) -> bool:
        """Manually trigger a scheduled review"""
        if name not in self.scheduled_reviews:
            return False

        review = self.scheduled_reviews[name]

        try:
            await self._execute_scheduled_review(review)
            review.last_run = datetime.now()
            self._save_schedules()
            return True

        except Exception as e:
            self.logger.error(f"Manual execution of '{name}' failed: {e}")
            return False
