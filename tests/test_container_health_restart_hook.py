"""
Tests for the Container Health Restart Hook.
"""

import pytest
import asyncio
import time
import json
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

# Add the .kiro directory to the Python path
kiro_path = Path(__file__).parent.parent / ".kiro"
sys.path.insert(0, str(kiro_path))

from engine.hooks.container_health_restart_hook import ContainerHealthRestartHook
from engine.core.models import HookContext
from engine.events.models import EventType


class TestContainerHealthRestartHook:
    """Test the ContainerHealthRestartHook class."""
    
    @pytest.fixture
    def hook_config(self):
        """Create a basic hook configuration."""
        return {
            "id": "test_health_hook",
            "name": "Test Health Hook",
            "enabled": True,
            "max_restart_attempts": 3,
            "restart_cooldown_seconds": 10,
            "notify_on_restart": True,
            "notify_on_failure": True,
            "excluded_containers": ["system-container"],
            "health_check_timeout": 5,
            "restart_timeout": 10
        }
    
    @pytest.fixture
    def hook(self, hook_config):
        """Create a hook instance."""
        return ContainerHealthRestartHook(hook_config)
    
    @pytest.fixture
    def unhealthy_context(self):
        """Create a context for unhealthy container events."""
        return HookContext(
            trigger_event={
                "type": EventType.SERVICE_HEALTH.value,
                "component": "container:web-app",
                "status": "unhealthy",
                "details": {"reason": "health check failed"}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    @pytest.fixture
    def failed_context(self):
        """Create a context for failed container events."""
        return HookContext(
            trigger_event={
                "type": EventType.SERVICE_HEALTH.value,
                "component": "container:database",
                "status": "failed",
                "details": {"reason": "container crashed"}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    @pytest.fixture
    def healthy_context(self):
        """Create a context for healthy container events."""
        return HookContext(
            trigger_event={
                "type": EventType.SERVICE_HEALTH.value,
                "component": "container:web-app",
                "status": "healthy",
                "details": {}
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
    
    def test_hook_initialization(self, hook, hook_config):
        """Test hook initialization."""
        assert hook.id == "test_health_hook"
        assert hook.name == "Test Health Hook"
        assert hook.enabled is True
        assert hook.max_restart_attempts == 3
        assert hook.restart_cooldown_seconds == 10
        assert hook.notify_on_restart is True
        assert hook.notify_on_failure is True
        assert "system-container" in hook.excluded_containers
        assert len(hook.restart_attempts) == 0
        assert len(hook.last_restart_time) == 0
    
    @pytest.mark.asyncio
    async def test_should_execute_unhealthy_container(self, hook, unhealthy_context):
        """Test that hook should execute for unhealthy containers."""
        result = await hook.should_execute(unhealthy_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_execute_failed_container(self, hook, failed_context):
        """Test that hook should execute for failed containers."""
        result = await hook.should_execute(failed_context)
        assert result is True
    
    @pytest.mark.asyncio
    async def test_should_not_execute_healthy_container(self, hook, healthy_context):
        """Test that hook should not execute for healthy containers."""
        result = await hook.should_execute(healthy_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_disabled_hook(self, hook_config, unhealthy_context):
        """Test that disabled hook should not execute."""
        hook_config["enabled"] = False
        hook = ContainerHealthRestartHook(hook_config)
        
        result = await hook.should_execute(unhealthy_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_wrong_event_type(self, hook):
        """Test that hook should not execute for wrong event types."""
        context = HookContext(
            trigger_event={
                "type": EventType.FILE_SAVE.value,
                "component": "container:web-app",
                "status": "unhealthy"
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_non_container_component(self, hook):
        """Test that hook should not execute for non-container components."""
        context = HookContext(
            trigger_event={
                "type": EventType.SERVICE_HEALTH.value,
                "component": "service:web-api",
                "status": "unhealthy"
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_excluded_container(self, hook):
        """Test that hook should not execute for excluded containers."""
        context = HookContext(
            trigger_event={
                "type": EventType.SERVICE_HEALTH.value,
                "component": "container:system-container",
                "status": "unhealthy"
            },
            project_state={},
            system_metrics={},
            user_preferences={}
        )
        
        result = await hook.should_execute(context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_max_attempts_reached(self, hook, unhealthy_context):
        """Test that hook should not execute when max attempts are reached."""
        # Set restart attempts to maximum
        hook.restart_attempts["web-app"] = hook.max_restart_attempts
        
        result = await hook.should_execute(unhealthy_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_should_not_execute_in_cooldown(self, hook, unhealthy_context):
        """Test that hook should not execute during cooldown period."""
        # Set last restart time to recent
        hook.last_restart_time["web-app"] = time.time()
        
        result = await hook.should_execute(unhealthy_context)
        assert result is False
    
    @pytest.mark.asyncio
    async def test_detect_container_runtime_podman(self, hook):
        """Test container runtime detection with podman available."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock successful podman version check
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"podman version", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            runtime = await hook._detect_container_runtime()
            assert runtime == "podman"
    
    @pytest.mark.asyncio
    async def test_detect_container_runtime_docker(self, hook):
        """Test container runtime detection with docker available."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            def mock_subprocess_call(*args, **kwargs):
                mock_process = AsyncMock()
                if args[0] == "podman":
                    # Podman fails
                    mock_process.returncode = 1
                    mock_process.communicate.return_value = (b"", b"command not found")
                else:
                    # Docker succeeds
                    mock_process.returncode = 0
                    mock_process.communicate.return_value = (b"docker version", b"")
                return mock_process
            
            mock_subprocess.side_effect = mock_subprocess_call
            
            runtime = await hook._detect_container_runtime()
            assert runtime == "docker"
    
    @pytest.mark.asyncio
    async def test_detect_container_runtime_none_available(self, hook):
        """Test container runtime detection with no runtime available."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            # Mock both podman and docker failing
            mock_process = AsyncMock()
            mock_process.returncode = 1
            mock_process.communicate.return_value = (b"", b"command not found")
            mock_subprocess.return_value = mock_process
            
            with pytest.raises(Exception) as exc_info:
                await hook._detect_container_runtime()
            
            assert "No container runtime" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_get_container_status(self, hook):
        """Test getting container status."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"running", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            status = await hook._get_container_status("docker", "test-container")
            assert status == "running"
    
    @pytest.mark.asyncio
    async def test_get_container_status_failure(self, hook):
        """Test getting container status when command fails."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"container not found")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            status = await hook._get_container_status("docker", "nonexistent-container")
            assert status == "unknown"
    
    @pytest.mark.asyncio
    async def test_restart_container_success(self, hook):
        """Test successful container restart."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"test-container", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            success, output = await hook._restart_container("docker", "test-container")
            assert success is True
            assert "test-container" in output
    
    @pytest.mark.asyncio
    async def test_restart_container_failure(self, hook):
        """Test failed container restart."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"restart failed")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            success, output = await hook._restart_container("docker", "test-container")
            assert success is False
            assert "restart failed" in output
    
    @pytest.mark.asyncio
    async def test_restart_container_timeout(self, hook):
        """Test container restart timeout."""
        hook.restart_timeout = 0.1  # Very short timeout
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            # Simulate long-running process that will timeout
            async def slow_communicate():
                await asyncio.sleep(1)  # Longer than timeout
                return (b"", b"")
            
            mock_process.communicate = slow_communicate
            mock_subprocess.return_value = mock_process
            
            success, output = await hook._restart_container("docker", "test-container")
            assert success is False
            assert "timed out" in output.lower()
    
    @pytest.mark.asyncio
    async def test_check_container_health_with_health_check(self, hook):
        """Test checking container health with health check available."""
        container_info = {
            "State": {
                "Health": {
                    "Status": "healthy"
                }
            }
        }
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (json.dumps([container_info]).encode(), b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            health = await hook._check_container_health("docker", "test-container")
            assert health == "healthy"
    
    @pytest.mark.asyncio
    async def test_check_container_health_without_health_check(self, hook):
        """Test checking container health without health check."""
        container_info = {
            "State": {
                "Status": "running"
            }
        }
        
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (json.dumps([container_info]).encode(), b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            health = await hook._check_container_health("docker", "test-container")
            assert health == "running"
    
    @pytest.mark.asyncio
    async def test_check_container_health_failure(self, hook):
        """Test checking container health when inspect fails."""
        with patch('asyncio.create_subprocess_exec') as mock_subprocess:
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"container not found")
            mock_process.returncode = 1
            mock_subprocess.return_value = mock_process
            
            health = await hook._check_container_health("docker", "nonexistent-container")
            assert health == "unknown"
    
    @pytest.mark.asyncio
    async def test_execute_successful_restart(self, hook, unhealthy_context):
        """Test successful hook execution with container restart."""
        with patch.object(hook, '_detect_container_runtime', return_value="docker"), \
             patch.object(hook, '_get_container_status', return_value="unhealthy"), \
             patch.object(hook, '_restart_container', return_value=(True, "container restarted")), \
             patch.object(hook, '_check_container_health', return_value="healthy"), \
             patch.object(hook, '_send_notification') as mock_notify:
            
            result = await hook.execute(unhealthy_context)
            
            assert result.success is True
            assert "Successfully restarted container web-app" in result.message
            assert len(result.actions_taken) > 0
            assert "Restarted container web-app" in result.actions_taken[0]
            assert result.execution_time_ms is not None
            assert hook.restart_attempts["web-app"] == 0  # Reset after success
            
            # Check notification was sent
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_restart_but_still_unhealthy(self, hook, unhealthy_context):
        """Test hook execution when restart succeeds but container is still unhealthy."""
        with patch.object(hook, '_detect_container_runtime', return_value="docker"), \
             patch.object(hook, '_get_container_status', return_value="unhealthy"), \
             patch.object(hook, '_restart_container', return_value=(True, "container restarted")), \
             patch.object(hook, '_check_container_health', return_value="unhealthy"), \
             patch.object(hook, '_send_notification') as mock_notify:
            
            result = await hook.execute(unhealthy_context)
            
            assert result.success is False
            assert "still unhealthy" in result.message
            assert len(result.suggestions) > 0
            assert hook.restart_attempts["web-app"] == 1  # Not reset
            
            # Check notification was sent
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_restart_failure(self, hook, unhealthy_context):
        """Test hook execution when container restart fails."""
        with patch.object(hook, '_detect_container_runtime', return_value="docker"), \
             patch.object(hook, '_get_container_status', return_value="unhealthy"), \
             patch.object(hook, '_restart_container', return_value=(False, "restart failed")), \
             patch.object(hook, '_send_notification') as mock_notify:
            
            result = await hook.execute(unhealthy_context)
            
            assert result.success is False
            assert "Failed to restart container web-app" in result.message
            assert result.error is not None
            assert len(result.suggestions) > 0
            assert hook.restart_attempts["web-app"] == 1
            
            # Check notification was sent
            mock_notify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_execute_runtime_detection_failure(self, hook, unhealthy_context):
        """Test hook execution when container runtime detection fails."""
        with patch.object(hook, '_detect_container_runtime', side_effect=Exception("No runtime available")):
            
            result = await hook.execute(unhealthy_context)
            
            assert result.success is False
            assert "Error executing container health restart hook" in result.message
            assert result.error is not None
    
    @pytest.mark.asyncio
    async def test_send_notification(self, hook):
        """Test notification sending."""
        # This is a simple test since the current implementation just logs
        await hook._send_notification("Test notification", {"container": "test"})
        # No assertion needed as it just logs
    
    def test_get_container_stats(self, hook):
        """Test getting container statistics."""
        # Set up some test data
        hook.restart_attempts = {"container1": 2, "container2": 3, "container3": 1}
        hook.last_restart_time = {"container1": time.time() - 5}  # In cooldown
        
        stats = hook.get_container_stats()
        
        assert stats["total_containers_monitored"] == 3
        assert stats["total_restart_attempts"] == 6
        assert stats["containers_at_max_attempts"] == 1  # container2 has 3 attempts
        assert stats["average_attempts_per_container"] == 2.0
        assert stats["containers_in_cooldown"] == 1  # container1
    
    def test_reset_container_attempts(self, hook):
        """Test resetting container restart attempts."""
        # Set up test data
        hook.restart_attempts["test-container"] = 3
        
        # Reset attempts
        result = hook.reset_container_attempts("test-container")
        assert result is True
        assert hook.restart_attempts["test-container"] == 0
        
        # Try to reset non-existent container
        result = hook.reset_container_attempts("nonexistent-container")
        assert result is False
    
    def test_get_container_restart_history(self, hook):
        """Test getting container restart history."""
        # Set up test data
        hook.restart_attempts["test-container"] = 2
        hook.last_restart_time["test-container"] = time.time() - 5
        hook.container_status_cache["test-container"] = "running"
        
        history = hook.get_container_restart_history("test-container")
        
        assert history["container_name"] == "test-container"
        assert history["restart_attempts"] == 2
        assert history["last_restart_time"] is not None
        assert history["current_status"] == "running"
        assert history["is_excluded"] is False
        assert history["is_in_cooldown"] is True  # Recent restart
        assert history["at_max_attempts"] is False
    
    def test_get_resource_requirements(self, hook):
        """Test resource requirements."""
        requirements = hook.get_resource_requirements()
        
        assert "cpu" in requirements
        assert "memory_mb" in requirements
        assert "disk_mb" in requirements
        assert "network" in requirements
        assert requirements["cpu"] > 0
        assert requirements["memory_mb"] > 0
        assert requirements["network"] is False  # Container restart doesn't need network
    
    @pytest.mark.asyncio
    async def test_cooldown_behavior(self, hook, unhealthy_context):
        """Test cooldown behavior between restarts."""
        # First execution should proceed
        result1 = await hook.should_execute(unhealthy_context)
        assert result1 is True
        
        # Simulate restart attempt
        hook.last_restart_time["web-app"] = time.time()
        hook.restart_attempts["web-app"] = 1
        
        # Second execution should be blocked by cooldown
        result2 = await hook.should_execute(unhealthy_context)
        assert result2 is False
        
        # After cooldown period, should execute again
        hook.last_restart_time["web-app"] = time.time() - (hook.restart_cooldown_seconds + 1)
        result3 = await hook.should_execute(unhealthy_context)
        assert result3 is True
    
    @pytest.mark.asyncio
    async def test_max_attempts_behavior(self, hook, unhealthy_context):
        """Test maximum restart attempts behavior."""
        # Set attempts to just below maximum
        hook.restart_attempts["web-app"] = hook.max_restart_attempts - 1
        
        # Should still execute
        result1 = await hook.should_execute(unhealthy_context)
        assert result1 is True
        
        # Set attempts to maximum
        hook.restart_attempts["web-app"] = hook.max_restart_attempts
        
        # Should not execute
        result2 = await hook.should_execute(unhealthy_context)
        assert result2 is False
    
    @pytest.mark.asyncio
    async def test_different_unhealthy_statuses(self, hook):
        """Test that hook responds to different unhealthy status values."""
        unhealthy_statuses = ["unhealthy", "failed", "error", "critical"]
        
        for status in unhealthy_statuses:
            context = HookContext(
                trigger_event={
                    "type": EventType.SERVICE_HEALTH.value,
                    "component": f"container:test-{status}",
                    "status": status
                },
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            
            result = await hook.should_execute(context)
            assert result is True, f"Hook should execute for status: {status}"
    
    @pytest.mark.asyncio
    async def test_healthy_statuses_ignored(self, hook):
        """Test that hook ignores healthy status values."""
        healthy_statuses = ["healthy", "running", "starting", "ok"]
        
        for status in healthy_statuses:
            context = HookContext(
                trigger_event={
                    "type": EventType.SERVICE_HEALTH.value,
                    "component": f"container:test-{status}",
                    "status": status
                },
                project_state={},
                system_metrics={},
                user_preferences={}
            )
            
            result = await hook.should_execute(context)
            assert result is False, f"Hook should not execute for status: {status}"