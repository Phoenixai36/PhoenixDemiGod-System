"""
Tests for automation scheduler module
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
from pathlib import Path
import json
import tempfile

from phoenix_system_review.automation.scheduler import (
    ReviewScheduler, ScheduledReview, ScheduleType
)
from phoenix_system_review.core.system_controller import SystemReviewController
from phoenix_system_review.models.data_models import ComponentCategory


class TestReviewScheduler:
    """Test cases for ReviewScheduler class"""

    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_controller(self):
        """Create mock system controller"""
        controller = Mock(spec=SystemReviewController)
        controller.configure = AsyncMock()
        controller.discover_components = AsyncMock(return_value={})
        controller.analyze_components = AsyncMock(return_value={})
        controller.assess_completion = AsyncMock(
            return_value={'overall_completion': 95.0, 'gaps': []})
        controller.generate_reports = AsyncMock(
            return_value={'todo': 'test report'})
        return controller

    @pytest.fixture
    def scheduler(self, mock_controller, temp_config_dir):
        """Create scheduler instance for testing"""
        return ReviewScheduler(mock_controller, temp_config_dir)

    def test_scheduler_initialization(self, scheduler, temp_config_dir):
        """Test scheduler initialization"""
        assert scheduler.config_dir == temp_config_dir
        assert scheduler.running is False
        assert len(scheduler.scheduled_reviews) == 0

    def test_add_schedule(self, scheduler):
        """Test adding a scheduled review"""
        review = scheduler.add_schedule(
            name="test_review",
            schedule_type=ScheduleType.DAILY,
            components=[ComponentCategory.INFRASTRUCTURE]
        )

        assert review.name == "test_review"
        assert review.schedule_type == ScheduleType.DAILY
        assert review.interval_minutes == 24 * 60  # Daily
        assert ComponentCategory.INFRASTRUCTURE in review.components
        assert review.enabled is True
        assert review.next_run is not None

    def test_add_custom_schedule(self, scheduler):
        """Test adding custom interval schedule"""
        review = scheduler.add_schedule(
            name="custom_review",
            schedule_type=ScheduleType.CUSTOM,
            interval_minutes=120,  # 2 hours
            output_format="json"
        )

        assert review.interval_minutes == 120
        assert review.output_format == "json"

    def test_remove_schedule(self, scheduler):
        """Test removing a scheduled review"""
        # Add a schedule first
        scheduler.add_schedule("test_review", ScheduleType.HOURLY)
        assert "test_review" in scheduler.scheduled_reviews

        # Remove it
        result = scheduler.remove_schedule("test_review")
        assert result is True
        assert "test_review" not in scheduler.scheduled_reviews

        # Try to remove non-existent schedule
        result = scheduler.remove_schedule("non_existent")
        assert result is False

    def test_enable_disable_schedule(self, scheduler):
        """Test enabling and disabling schedules"""
        scheduler.add_schedule("test_review", ScheduleType.HOURLY)

        # Disable
        result = scheduler.disable_schedule("test_review")
        assert result is True
        assert scheduler.scheduled_reviews["test_review"].enabled is False

        # Enable
        result = scheduler.enable_schedule("test_review")
        assert result is True
        assert scheduler.scheduled_reviews["test_review"].enabled is True

    def test_list_schedules(self, scheduler):
        """Test listing all schedules"""
        scheduler.add_schedule("review1", ScheduleType.HOURLY)
        scheduler.add_schedule("review2", ScheduleType.DAILY)

        schedules = scheduler.list_schedules()
        assert len(schedules) == 2
        assert any(s.name == "review1" for s in schedules)
        assert any(s.name == "review2" for s in schedules)

    @pytest.mark.asyncio
    async def test_start_stop_scheduler(self, scheduler):
        """Test starting and stopping scheduler"""
        # Start scheduler
        await scheduler.start_scheduler()
        assert scheduler.running is True
        assert scheduler.scheduler_task is not None

        # Stop scheduler
        await scheduler.stop_scheduler()
        assert scheduler.running is False

    @pytest.mark.asyncio
    async def test_execute_scheduled_review(self, scheduler, mock_controller):
        """Test executing a scheduled review"""
        review = ScheduledReview(
            name="test_review",
            schedule_type=ScheduleType.HOURLY,
            interval_minutes=60,
            output_format="json"
        )

        with patch('pathlib.Path.mkdir'), \
                patch('builtins.open', create=True), \
                patch('json.dump'):

            await scheduler._execute_scheduled_review(review)

            # Verify controller methods were called
            mock_controller.configure.assert_called_once()
            mock_controller.discover_components.assert_called_once()
            mock_controller.analyze_components.assert_called_once()
            mock_controller.assess_completion.assert_called_once()
            mock_controller.generate_reports.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_schedule_now(self, scheduler, mock_controller):
        """Test manually running a schedule"""
        scheduler.add_schedule("test_review", ScheduleType.HOURLY)

        with patch.object(scheduler, '_execute_scheduled_review', new_callable=AsyncMock) as mock_execute:
            result = await scheduler.run_schedule_now("test_review")

            assert result is True
            mock_execute.assert_called_once()

        # Test non-existent schedule
        result = await scheduler.run_schedule_now("non_existent")
        assert result is False

    def test_save_load_schedules(self, scheduler, temp_config_dir):
        """Test saving and loading schedules"""
        # Add some schedules
        scheduler.add_schedule("review1", ScheduleType.DAILY, components=[
                               ComponentCategory.INFRASTRUCTURE])
        scheduler.add_schedule(
            "review2", ScheduleType.WEEKLY, output_format="markdown")

        # Save schedules
        scheduler._save_schedules()

        # Create new scheduler and load
        new_scheduler = ReviewScheduler(Mock(), temp_config_dir)

        assert len(new_scheduler.scheduled_reviews) == 2
        assert "review1" in new_scheduler.scheduled_reviews
        assert "review2" in new_scheduler.scheduled_reviews

        review1 = new_scheduler.scheduled_reviews["review1"]
        assert review1.schedule_type == ScheduleType.DAILY
        assert ComponentCategory.INFRASTRUCTURE in review1.components

    @pytest.mark.asyncio
    async def test_send_notifications(self, scheduler):
        """Test sending webhook notifications"""
        review = ScheduledReview(
            name="test_review",
            schedule_type=ScheduleType.HOURLY,
            interval_minutes=60,
            notification_webhooks=["http://example.com/webhook"]
        )

        assessment_results = {
            'overall_completion': 95.0,
            'gaps': []
        }

        reports = {'todo': 'test report'}

        with patch('aiohttp.ClientSession') as mock_session:
            mock_response = Mock()
            mock_response.status = 200
            mock_session.return_value.__aenter__.return_value.post.return_value.__aenter__.return_value = mock_response

            await scheduler._send_notifications(review, assessment_results, reports)

            # Verify webhook was called
            mock_session.return_value.__aenter__.return_value.post.assert_called_once()


class TestScheduledReview:
    """Test cases for ScheduledReview dataclass"""

    def test_scheduled_review_creation(self):
        """Test creating a ScheduledReview"""
        review = ScheduledReview(
            name="test",
            schedule_type=ScheduleType.DAILY,
            interval_minutes=1440
        )

        assert review.name == "test"
        assert review.schedule_type == ScheduleType.DAILY
        assert review.interval_minutes == 1440
        assert review.enabled is True
        assert review.notification_webhooks == []

    def test_scheduled_review_with_components(self):
        """Test ScheduledReview with specific components"""
        review = ScheduledReview(
            name="test",
            schedule_type=ScheduleType.HOURLY,
            interval_minutes=60,
            components=[ComponentCategory.INFRASTRUCTURE,
                        ComponentCategory.MONETIZATION]
        )

        assert len(review.components) == 2
        assert ComponentCategory.INFRASTRUCTURE in review.components
        assert ComponentCategory.MONETIZATION in review.components


@pytest.mark.asyncio
async def test_scheduler_integration():
    """Integration test for scheduler functionality"""
    with tempfile.TemporaryDirectory() as temp_dir:
        config_dir = Path(temp_dir)
        mock_controller = Mock(spec=SystemReviewController)
        mock_controller.configure = AsyncMock()
        mock_controller.discover_components = AsyncMock(return_value={})
        mock_controller.analyze_components = AsyncMock(return_value={})
        mock_controller.assess_completion = AsyncMock(
            return_value={'overall_completion': 95.0, 'gaps': []})
        mock_controller.generate_reports = AsyncMock(
            return_value={'todo': 'test'})

        scheduler = ReviewScheduler(mock_controller, config_dir)

        # Add a schedule
        scheduler.add_schedule(
            "integration_test", ScheduleType.CUSTOM, interval_minutes=1)

        # Start scheduler briefly
        await scheduler.start_scheduler()

        # Let it run for a short time
        await asyncio.sleep(0.1)

        # Stop scheduler
        await scheduler.stop_scheduler()

        # Verify schedule was saved
        schedule_file = config_dir / "schedules.json"
        assert schedule_file.exists()

        with open(schedule_file, 'r') as f:
            saved_data = json.load(f)
            assert "integration_test" in saved_data
