"""
Integration tests for Phoenix Hydra System Review CLI

Tests the command-line interface functionality including argument parsing,
command execution, and output formatting.
"""

from phoenix_system_review.models.data_models import Priority, Issue, Component, ComponentStatus, EvaluationResult
from phoenix_system_review.cli_config import ConfigManager, CLIConfig
from phoenix_system_review.cli import PhoenixSystemReviewCLI
import pytest
import json
import yaml
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))


class TestPhoenixSystemReviewCLI:
    """Test cases for the CLI application."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance for testing."""
        return PhoenixSystemReviewCLI()

    @pytest.fixture
    def temp_project_dir(self):
        """Create temporary project directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)

            # Create basic project structure
            (project_path / 'src').mkdir()
            (project_path / 'infra').mkdir()
            (project_path / 'configs').mkdir()

            # Create sample configuration files
            compose_content = {
                'version': '3.8',
                'services': {
                    'phoenix-core': {
                        'image': 'phoenix-core:latest',
                        'ports': ['8080:8080']
                    }
                }
            }

            with open(project_path / 'infra' / 'compose.yaml', 'w') as f:
                yaml.dump(compose_content, f)

            yield str(project_path)

    @pytest.fixture
    def mock_engine(self):
        """Create mock system review engine."""
        engine = Mock()

        # Mock comprehensive review result
        mock_component = Component(
            name="test_component",
            category="infrastructure",
            path="/test/path",
            status=ComponentStatus.OPERATIONAL
        )

        mock_result = Mock()
        mock_result.overall_completion_percentage = 75.5
        mock_result.component_results = [
            EvaluationResult(
                component=mock_component,
                criteria_met=["criterion1", "criterion2"],
                criteria_missing=["criterion3"],
                completion_percentage=80.0,
                quality_score=0.85,
                issues=[
                    Issue(
                        severity=Priority.HIGH,
                        description="Test issue",
                        component="test_component",
                        recommendation="Fix test issue"
                    )
                ]
            )
        ]

        engine.run_comprehensive_review.return_value = mock_result
        engine.get_system_status.return_value = {
            'overall_health': 'healthy',
            'completion_percentage': 75.5,
            'active_issues': 1,
            'components': {
                'test_component': {
                    'status': 'operational',
                    'completion': 80.0
                }
            }
        }

        engine.generate_todo_list.return_value = []
        engine.check_service_health.return_value = {
            'healthy': True,
            'version': '1.0.0',
            'response_time': 0.1
        }

        engine.validate_system_configuration.return_value = {
            'valid': True,
            'issues': []
        }

        return engine

    def test_parser_creation(self, cli):
        """Test argument parser creation."""
        parser = cli.create_parser()

        # Test that parser was created
        assert parser is not None
        assert parser.prog == 'phoenix-review'

        # Test that subcommands exist
        subparsers_actions = [
            action for action in parser._actions
            if isinstance(action, argparse._SubParsersAction)
        ]
        assert len(subparsers_actions) == 1

        subparser = subparsers_actions[0]
        commands = list(subparser.choices.keys())
        expected_commands = ['analyze', 'report', 'status',
                             'todo', 'health-check', 'validate', 'init']

        for cmd in expected_commands:
            assert cmd in commands

    def test_analyze_command_parsing(self, cli):
        """Test analyze command argument parsing."""
        parser = cli.create_parser()

        # Test basic analyze command
        args = parser.parse_args(['analyze'])
        assert args.command == 'analyze'
        assert args.path == '.'
        assert args.components is None
        assert args.skip_tests is False
        assert args.deep_scan is False

        # Test analyze with options
        args = parser.parse_args([
            'analyze', '/test/path',
            '--components', 'podman', 'n8n',
            '--skip-tests',
            '--deep-scan'
        ])
        assert args.command == 'analyze'
        assert args.path == '/test/path'
        assert args.components == ['podman', 'n8n']
        assert args.skip_tests is True
        assert args.deep_scan is True

    def test_report_command_parsing(self, cli):
        """Test report command argument parsing."""
        parser = cli.create_parser()

        # Test basic report command
        args = parser.parse_args(['report'])
        assert args.command == 'report'
        assert args.type == 'summary'
        assert args.include_recommendations is False
        assert args.include_metrics is False

        # Test report with options
        args = parser.parse_args([
            'report',
            '--type', 'detailed',
            '--include-recommendations',
            '--include-metrics'
        ])
        assert args.command == 'report'
        assert args.type == 'detailed'
        assert args.include_recommendations is True
        assert args.include_metrics is True

    def test_status_command_parsing(self, cli):
        """Test status command argument parsing."""
        parser = cli.create_parser()

        # Test basic status command
        args = parser.parse_args(['status'])
        assert args.command == 'status'
        assert args.component is None
        assert args.summary is False

        # Test status with options
        args = parser.parse_args([
            'status',
            '--component', 'podman',
            '--summary'
        ])
        assert args.command == 'status'
        assert args.component == 'podman'
        assert args.summary is True

    def test_todo_command_parsing(self, cli):
        """Test todo command argument parsing."""
        parser = cli.create_parser()

        # Test basic todo command
        args = parser.parse_args(['todo'])
        assert args.command == 'todo'
        assert args.priority == 'all'
        assert args.component is None
        assert args.assignable is False

        # Test todo with options
        args = parser.parse_args([
            'todo',
            '--priority', 'high',
            '--component', 'podman',
            '--assignable'
        ])
        assert args.command == 'todo'
        assert args.priority == 'high'
        assert args.component == 'podman'
        assert args.assignable is True

    def test_health_check_command_parsing(self, cli):
        """Test health-check command argument parsing."""
        parser = cli.create_parser()

        # Test basic health-check command
        args = parser.parse_args(['health-check'])
        assert args.command == 'health-check'
        assert args.services == ['all']
        assert args.timeout == 30

        # Test health-check with options
        args = parser.parse_args([
            'health-check',
            '--services', 'podman', 'n8n',
            '--timeout', '60'
        ])
        assert args.command == 'health-check'
        assert args.services == ['podman', 'n8n']
        assert args.timeout == 60

    def test_validate_command_parsing(self, cli):
        """Test validate command argument parsing."""
        parser = cli.create_parser()

        # Test basic validate command
        args = parser.parse_args(['validate'])
        assert args.command == 'validate'
        assert args.fix is False
        assert args.strict is False

        # Test validate with options
        args = parser.parse_args([
            'validate',
            '--fix',
            '--strict'
        ])
        assert args.command == 'validate'
        assert args.fix is True
        assert args.strict is True

    def test_init_command_parsing(self, cli):
        """Test init command argument parsing."""
        parser = cli.create_parser()

        # Test basic init command
        args = parser.parse_args(['init'])
        assert args.command == 'init'
        assert args.template == 'basic'

        # Test init with template
        args = parser.parse_args([
            'init',
            '--template', 'enterprise'
        ])
        assert args.command == 'init'
        assert args.template == 'enterprise'

    def test_global_options_parsing(self, cli):
        """Test global options parsing."""
        parser = cli.create_parser()

        # Test global options
        args = parser.parse_args([
            '--project-root', '/test/project',
            '--config', '/test/config.yaml',
            '--verbose', '--verbose',
            '--output', '/test/output.json',
            '--format', 'json',
            'analyze'
        ])

        assert args.project_root == '/test/project'
        assert args.config == '/test/config.yaml'
        assert args.verbose == 2
        assert args.output == '/test/output.json'
        assert args.format == 'json'
        assert args.command == 'analyze'

    @patch('phoenix_system_review.cli.SystemReviewEngine')
    @patch('phoenix_system_review.cli.ReportGenerator')
    def test_analyze_command_execution(self, mock_report_gen, mock_engine_class, cli, mock_engine, temp_project_dir):
        """Test analyze command execution."""
        mock_engine_class.return_value = mock_engine
        mock_report_gen.return_value = Mock()

        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['--project-root', temp_project_dir, 'analyze'])

        assert result == 0
        mock_engine.run_comprehensive_review.assert_called_once()

        # Check that output was generated
        output = mock_stdout.getvalue()
        assert 'Phoenix Hydra System Review Report' in output

    @patch('phoenix_system_review.cli.SystemReviewEngine')
    @patch('phoenix_system_review.cli.ReportGenerator')
    def test_status_command_execution(self, mock_report_gen, mock_engine_class, cli, mock_engine, temp_project_dir):
        """Test status command execution."""
        mock_engine_class.return_value = mock_engine
        mock_report_gen.return_value = Mock()

        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['--project-root', temp_project_dir, 'status'])

        assert result == 0
        mock_engine.get_system_status.assert_called_once()

        # Check that output was generated
        output = mock_stdout.getvalue()
        assert 'Phoenix Hydra System Review Report' in output

    @patch('phoenix_system_review.cli.SystemReviewEngine')
    @patch('phoenix_system_review.cli.ReportGenerator')
    def test_health_check_command_execution(self, mock_report_gen, mock_engine_class, cli, mock_engine, temp_project_dir):
        """Test health-check command execution."""
        mock_engine_class.return_value = mock_engine
        mock_report_gen.return_value = Mock()

        # Capture stdout
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            result = cli.run(['--project-root', temp_project_dir,
                             'health-check', '--services', 'podman'])

        assert result == 0
        mock_engine.check_service_health.assert_called_with(
            'podman', timeout=30)

        # Check that output was generated
        output = mock_stdout.getvalue()
        assert 'Phoenix Hydra System Review Report' in output

    def test_output_formatting_json(self, cli):
        """Test JSON output formatting."""
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'summary': 'Test summary',
            'components': {
                'test': {'status': 'operational'}
            }
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._output_result(test_data, 'json')

        output = mock_stdout.getvalue()
        parsed_output = json.loads(output)

        assert parsed_output['timestamp'] == '2024-01-01T00:00:00'
        assert parsed_output['summary'] == 'Test summary'
        assert parsed_output['components']['test']['status'] == 'operational'

    def test_output_formatting_yaml(self, cli):
        """Test YAML output formatting."""
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'summary': 'Test summary'
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._output_result(test_data, 'yaml')

        output = mock_stdout.getvalue()
        parsed_output = yaml.safe_load(output)

        assert parsed_output['timestamp'] == '2024-01-01T00:00:00'
        assert parsed_output['summary'] == 'Test summary'

    def test_output_formatting_markdown(self, cli):
        """Test Markdown output formatting."""
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'summary': 'Test summary',
            'components': {
                'test': {'status': 'operational'}
            }
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._output_result(test_data, 'markdown')

        output = mock_stdout.getvalue()

        assert '# Phoenix Hydra System Review Report' in output
        assert '**Generated:** 2024-01-01T00:00:00' in output
        assert '## Summary' in output
        assert 'Test summary' in output
        assert '### Test' in output

    def test_output_formatting_html(self, cli):
        """Test HTML output formatting."""
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'summary': 'Test summary'
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._output_result(test_data, 'html')

        output = mock_stdout.getvalue()

        assert '<!DOCTYPE html>' in output
        assert '<title>Phoenix Hydra System Review Report</title>' in output
        assert '<strong>Generated:</strong> 2024-01-01T00:00:00' in output
        assert 'Test summary' in output

    def test_output_formatting_text(self, cli):
        """Test text output formatting."""
        test_data = {
            'timestamp': '2024-01-01T00:00:00',
            'summary': 'Test summary',
            'components': {
                'test': {'status': 'operational'}
            }
        }

        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            cli._output_result(test_data, 'text')

        output = mock_stdout.getvalue()

        assert 'Phoenix Hydra System Review Report' in output
        assert 'Generated: 2024-01-01T00:00:00' in output
        assert 'Summary:' in output
        assert 'Test summary' in output
        assert 'TEST:' in output
        assert 'Status: operational' in output

    def test_output_to_file(self, cli):
        """Test output to file."""
        test_data = {'test': 'data'}

        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as temp_file:
            temp_path = temp_file.name

        try:
            cli._output_result(test_data, 'json', temp_path)

            # Verify file was created and contains correct data
            with open(temp_path, 'r') as f:
                file_content = json.load(f)

            assert file_content == test_data

        finally:
            Path(temp_path).unlink(missing_ok=True)

    def test_init_command_execution(self, cli, temp_project_dir):
        """Test init command execution."""
        config_path = Path(temp_project_dir) / '.phoenix-review.yaml'

        # Mock user input to not overwrite
        with patch('builtins.input', return_value='y'):
            with patch('os.getcwd', return_value=temp_project_dir):
                result = cli.run(['init', '--template', 'advanced'])

        assert result == 0
        assert config_path.exists()

        # Verify configuration content
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)

        assert config_data['project']['name'] == 'Phoenix Hydra'
        assert config_data['analysis']['deep_scan'] is True
        assert config_data['reporting']['include_metrics'] is True

    def test_error_handling_invalid_command(self, cli):
        """Test error handling for invalid commands."""
        result = cli.run(['invalid-command'])
        assert result == 1

    def test_error_handling_missing_project_root(self, cli):
        """Test error handling for missing project root."""
        result = cli.run(['--project-root', '/nonexistent/path', 'analyze'])
        assert result == 1

    def test_keyboard_interrupt_handling(self, cli):
        """Test keyboard interrupt handling."""
        with patch('phoenix_system_review.cli.SystemReviewEngine') as mock_engine_class:
            mock_engine_class.side_effect = KeyboardInterrupt()

            result = cli.run(['analyze'])
            assert result == 130  # Standard exit code for SIGINT

    def test_verbose_logging(self, cli):
        """Test verbose logging configuration."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            cli._set_log_level(3, False)  # -vvv

            # Verify debug level was set
            import logging
            logging.getLogger().setLevel.assert_called_with(logging.DEBUG)

    def test_quiet_logging(self, cli):
        """Test quiet logging configuration."""
        with patch('logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            cli._set_log_level(0, True)  # --quiet

            # Verify error level was set
            import logging
            logging.getLogger().setLevel.assert_called_with(logging.ERROR)


class TestCLIIntegration:
    """Integration tests that test the CLI with real components."""

    @pytest.fixture
    def real_project_dir(self):
        """Use the actual project directory for integration tests."""
        return str(Path(__file__).parent.parent.parent)

    def test_cli_script_execution(self, real_project_dir):
        """Test that the CLI script can be executed."""
        script_path = Path(real_project_dir) / 'scripts' / 'phoenix-review'

        # Make script executable
        script_path.chmod(0o755)

        # Test help command
        result = subprocess.run([
            sys.executable, str(script_path), '--help'
        ], capture_output=True, text=True, cwd=real_project_dir)

        assert result.returncode == 0
        assert 'Phoenix Hydra System Review CLI' in result.stdout
        assert 'analyze' in result.stdout
        assert 'report' in result.stdout

    def test_cli_init_real_execution(self, real_project_dir):
        """Test init command with real execution."""
        with tempfile.TemporaryDirectory() as temp_dir:
            script_path = Path(real_project_dir) / 'scripts' / 'phoenix-review'
            script_path.chmod(0o755)

            # Test init command
            result = subprocess.run([
                sys.executable, str(script_path),
                '--project-root', temp_dir,
                'init', '--template', 'basic'
            ], capture_output=True, text=True, cwd=real_project_dir)

            assert result.returncode == 0

            # Verify config file was created
            config_path = Path(temp_dir) / '.phoenix-review.yaml'
            assert config_path.exists()

            # Verify config content
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)

            assert config_data['project']['name'] == 'Phoenix Hydra'
            assert 'analysis' in config_data
            assert 'reporting' in config_data
