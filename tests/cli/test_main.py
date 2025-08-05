"""
Tests for CLI main module
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import json

from phoenix_system_review.cli.main import PhoenixReviewCLI


class TestPhoenixReviewCLI:
    """Test cases for PhoenixReviewCLI class"""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing"""
        return PhoenixReviewCLI()

    def test_create_parser(self, cli):
        """Test argument parser creation"""
        parser = cli.create_parser()

        # Test main parser
        assert parser.prog == 'phoenix-review'
        assert 'Phoenix Hydra System Review Tool' in parser.description

        # Test that subcommands are available
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert len(subparsers_actions) == 1

        subparser = subparsers_actions[0]
        assert 'review' in subparser.choices
        assert 'report' in subparser.choices
        assert 'status' in subparser.choices
        assert 'config' in subparser.choices

    def test_load_config_default(self, cli, tmp_path):
        """Test loading default configuration"""
        config_file = tmp_path / "phoenix-review.json"
        config = cli._load_config(config_file)

        # Should return default config when file doesn't exist
        assert 'project_path' in config
        assert 'output_directory' in config
        assert 'component_weights' in config
        assert 'service_endpoints' in config

    def test_load_config_from_file(self, cli, tmp_path):
        """Test loading configuration from file"""
        config_file = tmp_path / "phoenix-review.json"

        # Create test config file
        test_config = {
            "project_path": "/custom/path",
            "custom_setting": "test_value"
        }

        with open(config_file, 'w') as f:
            json.dump(test_config, f)

        config = cli._load_config(config_file)

        # Should merge with defaults
        assert config['project_path'] == "/custom/path"
        assert config['custom_setting'] == "test_value"
        assert 'output_directory' in config  # Default should still be present

    @pytest.mark.asyncio
    async def test_run_review_command(self, cli):
        """Test running review command"""
        with patch.object(cli.controller, 'configure', new_callable=AsyncMock) as mock_configure:
            with patch('phoenix_system_review.cli.commands.ReviewCommand.execute', new_callable=AsyncMock) as mock_execute:
                mock_execute.return_value = 0

                result = await cli.run(['review', '--format', 'json'])

                assert result == 0
                mock_execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_invalid_command(self, cli):
        """Test running with no command shows help"""
        with patch('sys.stdout'):  # Suppress help output
            result = await cli.run([])
            assert result == 1

    @pytest.mark.asyncio
    async def test_run_keyboard_interrupt(self, cli):
        """Test handling keyboard interrupt"""
        with patch.object(cli.controller, 'configure', new_callable=AsyncMock) as mock_configure:
            mock_configure.side_effect = KeyboardInterrupt()

            result = await cli.run(['review'])
            assert result == 130

    @pytest.mark.asyncio
    async def test_run_unexpected_error(self, cli):
        """Test handling unexpected errors"""
        with patch.object(cli.controller, 'configure', new_callable=AsyncMock) as mock_configure:
            mock_configure.side_effect = Exception("Test error")

            result = await cli.run(['review'])
            assert result == 1


@pytest.mark.asyncio
async def test_main_function():
    """Test main function entry point"""
    with patch('phoenix_system_review.cli.main.PhoenixReviewCLI') as mock_cli_class:
        mock_cli = Mock()
        mock_cli_class.return_value = mock_cli
        mock_cli.run = AsyncMock(return_value=0)

        with patch('sys.exit') as mock_exit:
            from phoenix_system_review.cli.main import main
            main()

            mock_cli.run.assert_called_once()
            mock_exit.assert_called_once_with(0)


def test_cli_integration():
    """Integration test for CLI argument parsing"""
    cli = PhoenixReviewCLI()
    parser = cli.create_parser()

    # Test review command parsing
    args = parser.parse_args(
        ['review', '--format', 'json', '--output-dir', 'test_reports'])
    assert args.command == 'review'
    assert args.format == 'json'
    assert args.output_dir == Path('test_reports')

    # Test report command parsing
    args = parser.parse_args(
        ['report', '--type', 'todo', '--priority', 'high'])
    assert args.command == 'report'
    assert args.type == 'todo'
    assert args.priority == 'high'

    # Test status command parsing
    args = parser.parse_args(['status', '--services', '--format', 'table'])
    assert args.command == 'status'
    assert args.services is True
    assert args.format == 'table'
