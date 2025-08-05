#!/usr/bin/env python3
"""
Unit tests for Phoenix Hydra Root Folder Refactoring Hook

Tests the core functionality of the refactoring system including:
- Directory analysis
- Plan generation
- Safety features
- Configuration handling

Author: Phoenix Hydra Team
Version: 1.0.0
"""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from hooks.refactor_root_folder import RefactorAction, RefactorPlan, RootFolderRefactor


class TestRootFolderRefactor(unittest.TestCase):
    """Test cases for RootFolderRefactor class"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())
        self.refactor = RootFolderRefactor(str(self.test_dir))

        # Create test directory structure
        self._create_test_structure()

    def tearDown(self):
        """Clean up test environment"""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def _create_test_structure(self):
        """Create a test directory structure"""
        # Create multiple virtual environments
        (self.test_dir / "venv").mkdir()
        (self.test_dir / ".venv").mkdir()
        (self.test_dir / "venv2").mkdir()

        # Create build outputs
        (self.test_dir / "build").mkdir()
        (self.test_dir / "build_output").mkdir()
        (self.test_dir / "dist").mkdir()
        (self.test_dir / "__pycache__").mkdir()

        # Create legacy directories
        (self.test_dir / "Nueva carpeta").mkdir()
        (self.test_dir / "BooPhoenix369").mkdir()

        # Create scattered config files
        (self.test_dir / "app.config.js").touch()
        (self.test_dir / "settings.ini").touch()

        # Create log files
        (self.test_dir / "app.log").touch()
        (self.test_dir / "error.log").touch()

        # Create some content in directories
        (self.test_dir / "venv" / "lib").mkdir()
        (self.test_dir / "venv" / "lib" / "python3.11").mkdir()
        (self.test_dir / "build_output" / "artifact.zip").touch()

    def test_analyze_virtual_environments(self):
        """Test virtual environment analysis"""
        actions = self.refactor._analyze_virtual_environments()

        # Should find actions to consolidate venvs
        self.assertGreater(len(actions), 0)

        # Should have move and delete actions
        action_types = [action.action_type for action in actions]
        self.assertIn("delete", action_types)

    def test_analyze_build_outputs(self):
        """Test build output analysis"""
        actions = self.refactor._analyze_build_outputs()

        # Should find actions to organize build outputs
        self.assertGreater(len(actions), 0)

        # Should include __pycache__ deletion
        pycache_actions = [a for a in actions if "__pycache__" in a.source_path]
        self.assertGreater(len(pycache_actions), 0)
        self.assertEqual(pycache_actions[0].action_type, "delete")

    def test_analyze_legacy_directories(self):
        """Test legacy directory analysis"""
        actions = self.refactor._analyze_legacy_directories()

        # Should find legacy directories to remove
        self.assertGreater(len(actions), 0)

        # Should target specific legacy directories
        legacy_actions = [
            a
            for a in actions
            if "Nueva carpeta" in a.source_path or "BooPhoenix369" in a.source_path
        ]
        self.assertGreater(len(legacy_actions), 0)

    def test_analyze_configuration_files(self):
        """Test configuration file analysis"""
        actions = self.refactor._analyze_configuration_files()

        # Should find config files to move
        config_actions = [
            a
            for a in actions
            if ".config.js" in a.source_path or ".ini" in a.source_path
        ]
        self.assertGreater(len(config_actions), 0)

        # Should be move actions to configs directory
        for action in config_actions:
            self.assertEqual(action.action_type, "move")
            self.assertIn("configs", action.target_path)

    def test_analyze_log_files(self):
        """Test log file analysis"""
        actions = self.refactor._analyze_log_files()

        # Should find log files to move
        log_actions = [a for a in actions if ".log" in a.source_path]
        self.assertGreater(len(log_actions), 0)

        # Should be move actions to logs directory
        for action in log_actions:
            self.assertEqual(action.action_type, "move")
            self.assertIn("logs", action.target_path)

    def test_full_analysis(self):
        """Test complete directory analysis"""
        plan = self.refactor.analyze_root_structure()

        # Should return a valid plan
        self.assertIsInstance(plan, RefactorPlan)
        self.assertGreater(len(plan.actions), 0)
        self.assertGreater(plan.total_files, 0)

        # Should have various action types
        action_types = set(action.action_type for action in plan.actions)
        self.assertIn("move", action_types)
        self.assertIn("delete", action_types)

    def test_directory_size_calculation(self):
        """Test directory size calculation"""
        # Create a file with known size
        test_file = self.test_dir / "test_file.txt"
        test_content = "x" * 1024  # 1KB
        test_file.write_text(test_content)

        size_mb, file_count = self.refactor._get_directory_size(self.test_dir)

        # Should calculate size and count correctly
        self.assertGreater(size_mb, 0)
        self.assertGreater(file_count, 0)

    def test_empty_directory_detection(self):
        """Test empty directory detection"""
        # Create empty directory
        empty_dir = self.test_dir / "empty_dir"
        empty_dir.mkdir()

        # Create directory with only hidden files
        hidden_dir = self.test_dir / "hidden_dir"
        hidden_dir.mkdir()
        (hidden_dir / ".hidden_file").touch()

        # Test detection
        self.assertTrue(self.refactor._is_empty_directory(empty_dir))
        self.assertTrue(self.refactor._is_empty_directory(hidden_dir))
        self.assertFalse(self.refactor._is_empty_directory(self.test_dir / "venv"))

    def test_backup_creation(self):
        """Test backup creation functionality"""
        plan = self.refactor.analyze_root_structure()

        # Create backup
        success = self.refactor.create_backup(plan)
        self.assertTrue(success)

        # Verify backup directory exists
        self.assertTrue(self.refactor.backup_dir.exists())

        # Verify manifest file exists
        manifest_file = self.refactor.backup_dir / "manifest.json"
        self.assertTrue(manifest_file.exists())

        # Verify manifest content
        with open(manifest_file) as f:
            manifest = json.load(f)

        self.assertIn("created_at", manifest)
        self.assertIn("actions", manifest)
        self.assertEqual(len(manifest["actions"]), len(plan.actions))

    @patch("shutil.move")
    def test_execute_move_action(self, mock_move):
        """Test move action execution"""
        action = RefactorAction(
            action_type="move",
            source_path=str(self.test_dir / "test_file.txt"),
            target_path=str(self.test_dir / "target" / "test_file.txt"),
            reason="Test move",
        )

        # Create source file
        Path(action.source_path).touch()

        # Execute move
        self.refactor._execute_move(action)

        # Verify move was called
        mock_move.assert_called_once()

    @patch("shutil.rmtree")
    def test_execute_delete_action(self, mock_rmtree):
        """Test delete action execution"""
        action = RefactorAction(
            action_type="delete",
            source_path=str(self.test_dir / "test_dir"),
            reason="Test delete",
        )

        # Create source directory
        Path(action.source_path).mkdir()

        # Execute delete
        self.refactor._execute_delete(action)

        # Verify rmtree was called
        mock_rmtree.assert_called_once()

    def test_configuration_loading(self):
        """Test configuration loading and merging"""
        # Create custom config
        config_dir = self.test_dir / ".kiro" / "hooks"
        config_dir.mkdir(parents=True)

        custom_config = {"virtual_environments": {"consolidate": False}}

        config_file = config_dir / "refactor_config.json"
        with open(config_file, "w") as f:
            json.dump(custom_config, f)

        # Create new refactor instance
        refactor = RootFolderRefactor(str(self.test_dir))

        # Verify custom config was loaded
        self.assertFalse(refactor.config["virtual_environments"]["consolidate"])

        # Verify defaults are still present
        self.assertIn("build_outputs", refactor.config)


class TestRefactorHookIntegration(unittest.TestCase):
    """Test cases for hook integration"""

    @patch("hooks.refactor_root_folder.RootFolderRefactor")
    def test_hook_execution(self, mock_refactor_class):
        """Test hook execution flow"""
        from hooks.refactor_root_folder import refactor_root_folder_hook

        # Mock refactor instance
        mock_refactor = MagicMock()
        mock_plan = MagicMock()
        mock_plan.actions = [MagicMock()]
        mock_refactor.analyze_root_structure.return_value = mock_plan
        mock_refactor.create_backup.return_value = True
        mock_refactor.execute_plan.return_value = True
        mock_refactor_class.return_value = mock_refactor

        # Execute hook
        import asyncio

        asyncio.run(refactor_root_folder_hook())

        # Verify methods were called
        mock_refactor.analyze_root_structure.assert_called_once()
        mock_refactor.create_backup.assert_called_once()
        mock_refactor.execute_plan.assert_called_once()


if __name__ == "__main__":
    unittest.main()
