"""
VS Code Task Integration for Phoenix Hydra System Review

Provides integration with VS Code tasks for manual and automated review execution,
with support for task definitions, progress reporting, and result display.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from ..core.system_controller import SystemController
from ..models.data_models import ComponentCategory


@dataclass
class VSCodeTask:
    """VS Code task definition"""
    label: str
    type: str
    command: str
    args: List[str]
    group: str = "build"
    presentation: Dict[str, Any] = None
    options: Dict[str, Any] = None

    def __post_init__(self):
        if self.presentation is None:
            self.presentation = {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "shared",
                "showReuseMessage": True,
                "clear": False
            }
        if self.options is None:
            self.options = {"cwd": "${workspaceFolder}"}


class VSCodeTaskIntegration:
    """
    Integration with VS Code tasks for Phoenix Hydra system review

    Features:
    - Automatic task.json generation
    - Phoenix-specific review tasks
    - Progress reporting in VS Code terminal
    - Integration with existing Phoenix tasks
    """

    def __init__(self, controller: SystemController, workspace_path: Path = None):
            self.controller = controller
        self.workspace_path = workspace_path or Path.cwd()
        self.vscode_dir = self.workspace_path / ".vscode"
        self.tasks_file = self.vscode_dir / "tasks.json"

        self.logger = logging.getLogger(__name__)

    def setup_tasks(self):
        """Set up VS Code tasks for Phoenix system review"""

        # Ensure .vscode directory exists
        self.vscode_dir.mkdir(exist_ok=True)

        # Load existing tasks or create new
        existing_tasks = self._load_existing_tasks()

        # Define Phoenix review tasks
        phoenix_tasks = self._create_phoenix_tasks()

        # Merge with existing tasks
        merged_tasks = self._merge_tasks(existing_tasks, phoenix_tasks)

        # Save updated tasks
        self._save_tasks(merged_tasks)

        self.logger.info(f"VS Code tasks configured in {self.tasks_file}")

    def _load_existing_tasks(self) -> Dict[str, Any]:
        """Load existing VS Code tasks"""
        if self.tasks_file.exists():
            try:
                with open(self.tasks_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Failed to load existing tasks: {e}")

        return {
            "version": "2.0.0",
            "tasks": []
        }

    def _create_phoenix_tasks(self) -> List[Dict[str, Any]]:
        """Create Phoenix-specific review tasks"""

        tasks = []

        # Full system review task
        tasks.append({
            "label": "Phoenix: Full System Review",
            "type": "shell",
            "command": "python",
            "args": [
                "-m", "phoenix_system_review.cli.main",
                "review",
                "--format", "markdown",
                "--output-dir", "reports/vscode"
            ],
            "group": {
                "kind": "build",
                "isDefault": True
            },
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": true,
                "panel": "new",
                "showReuseMessage": False,
                "clear": True
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "problemMatcher": [],
            "detail": "Execute comprehensive Phoenix Hydra system review"
        })

        # Quick status check
        tasks.append({
            "label": "Phoenix: Quick Status Check",
            "type": "shell",
            "command": "python",
            "args": [
                "-m", "phoenix_system_review.cli.main",
                "status",
                "--services",
                "--format", "table"
            ],
            "group": "test",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "shared",
                "showReuseMessage": True,
                "clear": False
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "detail": "Quick health check of Phoenix Hydra components"
        })

        # Generate TODO report
        tasks.append({
            "label": "Phoenix: Generate TODO Report",
            "type": "shell",
            "command": "python",
            "args": [
                "-m", "phoenix_system_review.cli.main",
                "report",
                "--type", "todo",
                "--format", "markdown",
                "--output", "reports/TODO.md"
            ],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "silent",
                "focus": False,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "detail": "Generate prioritized TODO checklist"
        })

        # Component-specific reviews
        for category in ComponentCategory:
            tasks.append({
                "label": f"Phoenix: Review {category.value.title()} Components",
                "type": "shell",
                "command": "python",
                "args": [
                    "-m", "phoenix_system_review.cli.main",
                    "review",
                    "--components", category.value,
                    "--format", "json",
                    "--output-dir", f"reports/{category.value}"
                ],
                "group": "build",
                "presentation": {
                    "echo": True,
                    "reveal": "silent",
                    "focus": False,
                    "panel": "shared"
                },
                "options": {
                    "cwd": "${workspaceFolder}"
                },
                "detail": f"Review only {category.value} components"
            })

        # Mamba/SSM specific tasks
        tasks.append({
            "label": "Phoenix: Mamba Integration Review",
            "type": "shell",
            "command": "python",
            "args": [
                "-m", "phoenix_system_review.cli.main",
                "review",
                "--components", "automation",
                "--format", "json",
                "--output-dir", "reports/mamba_integration"
            ],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": True,
                "panel": "new"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "detail": "Review Mamba/SSM integration and energy efficiency"
        })

        # Monetization review
        tasks.append({
            "label": "Phoenix: Monetization Review",
            "type": "shell",
            "command": "python",
            "args": [
                "-m", "phoenix_system_review.cli.main",
                "review",
                "--components", "monetization",
                "--format", "markdown",
                "--output-dir", "reports/monetization"
            ],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": True,
                "panel": "new"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "detail": "Review revenue streams and grant readiness"
        })

        # Continuous monitoring setup
        tasks.append({
            "label": "Phoenix: Start Continuous Monitoring",
            "type": "shell",
            "command": "python",
            "args": [
                "-c",
                "from phoenix_system_review.automation.monitoring import ContinuousMonitoring; import asyncio; asyncio.run(ContinuousMonitoring().start())"
            ],
            "group": "build",
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "dedicated"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            },
            "isBackground": True,
            "problemMatcher": {
                "pattern": {
                    "regexp": "^(.*):(\\d+):(\\d+):\\s+(warning|error):\\s+(.*)$",
                    "file": 1,
                    "line": 2,
                    "column": 3,
                    "severity": 4,
                    "message": 5
                },
                "background": {
                    "activeOnStart": True,
                    "beginsPattern": "^Starting Phoenix monitoring",
                    "endsPattern": "^Phoenix monitoring started"
                }
            },
            "detail": "Start continuous Phoenix system monitoring"
        })

        return tasks

    def _merge_tasks(self, existing: Dict[str, Any], phoenix_tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge Phoenix tasks with existing VS Code tasks"""

        # Get existing task labels to avoid duplicates
        existing_labels = {
            task.get('label', '') for task in existing.get('tasks', [])
        }

        # Filter out Phoenix tasks that already exist
        new_tasks = [
            task for task in phoenix_tasks
            if task['label'] not in existing_labels
        ]

        # Add new Phoenix tasks
        existing['tasks'].extend(new_tasks)

        # Ensure version is set
        existing['version'] = "2.0.0"

        return existing

    def _save_tasks(self, tasks: Dict[str, Any]):
        """Save tasks to VS Code tasks.json"""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(tasks, f, indent=2)
        except Exception as e:
            self.logger.error(f"Failed to save VS Code tasks: {e}")
            raise

    def create_custom_task(
        self,
        label: str,
        command: str,
        args: List[str],
        group: str = "build",
        detail: str = None
    ) -> Dict[str, Any]:
        """Create a custom Phoenix review task"""

        task = {
            "label": f"Phoenix: {label}",
            "type": "shell",
            "command": command,
            "args": args,
            "group": group,
            "presentation": {
                "echo": True,
                "reveal": "always",
                "focus": False,
                "panel": "shared"
            },
            "options": {
                "cwd": "${workspaceFolder}"
            }
        }

        if detail:
            task["detail"] = detail

        return task

    def add_task(self, task: Dict[str, Any]):
        """Add a single task to VS Code configuration"""
        existing_tasks = self._load_existing_tasks()
        existing_tasks['tasks'].append(task)
        self._save_tasks(existing_tasks)

    def remove_phoenix_tasks(self):
        """Remove all Phoenix-related tasks"""
        existing_tasks = self._load_existing_tasks()

        # Filter out Phoenix tasks
        filtered_tasks = [
            task for task in existing_tasks.get('tasks', [])
            if not task.get('label', '').startswith('Phoenix:')
        ]

        existing_tasks['tasks'] = filtered_tasks
        self._save_tasks(existing_tasks)

        self.logger.info(
            "Removed all Phoenix tasks from VS Code configuration")

    def get_task_status(self) -> Dict[str, Any]:
        """Get status of Phoenix tasks in VS Code"""
        existing_tasks = self._load_existing_tasks()

        phoenix_tasks = [
            task for task in existing_tasks.get('tasks', [])
            if task.get('label', '').startswith('Phoenix:')
        ]

        return {
            'total_tasks': len(existing_tasks.get('tasks', [])),
            'phoenix_tasks': len(phoenix_tasks),
            'phoenix_task_labels': [task['label'] for task in phoenix_tasks],
            'tasks_file_exists': self.tasks_file.exists()
        }
