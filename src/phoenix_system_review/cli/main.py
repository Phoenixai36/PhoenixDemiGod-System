#!/usr/bin/env python3
"""
Main CLI entry point for Phoenix Hydra System Review Tool

Usage:
    phoenix-review [COMMAND] [OPTIONS]

Commands:
    review      Execute comprehensive system review
    report      Generate specific reports
    status      Show current system status
    config      Manage configuration settings
    
Examples:
    phoenix-review review --output-format json
    phoenix-review report --type todo --priority high
    phoenix-review status --components infrastructure
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

from ..core.system_controller import SystemReviewController
from ..models.data_models import ComponentCategory, Priority
from .commands import ReviewCommand, ReportCommand, StatusCommand, ConfigCommand


class PhoenixReviewCLI:
    """Main CLI application class for Phoenix Hydra System Review"""

    def __init__(self):
        self.controller = SystemReviewController()
        self.logger = self._setup_logging()

    def _setup_logging(self) -> logging.Logger:
        """Configure logging for CLI operations"""
        logger = logging.getLogger('phoenix_review_cli')
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the main argument parser"""
        parser = argparse.ArgumentParser(
            prog='phoenix-review',
            description='Phoenix Hydra System Review Tool',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  phoenix-review review --output reports/
  phoenix-review report --type todo --format json
  phoenix-review status --verbose
  phoenix-review config --set project_path=/path/to/phoenix
            """
        )

        parser.add_argument(
            '--version',
            action='version',
            version='%(prog)s 1.0.0'
        )

        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Enable verbose output'
        )

        parser.add_argument(
            '--config-file',
            type=Path,
            default=Path.cwd() / 'phoenix-review.json',
            help='Configuration file path (default: phoenix-review.json)'
        )

        # Create subparsers for commands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )

        # Review command
        review_parser = subparsers.add_parser(
            'review',
            help='Execute comprehensive system review'
        )
        ReviewCommand.add_arguments(review_parser)

        # Report command
        report_parser = subparsers.add_parser(
            'report',
            help='Generate specific reports'
        )
        ReportCommand.add_arguments(report_parser)

        # Status command
        status_parser = subparsers.add_parser(
            'status',
            help='Show current system status'
        )
        StatusCommand.add_arguments(status_parser)

        # Config command
        config_parser = subparsers.add_parser(
            'config',
            help='Manage configuration settings'
        )
        ConfigCommand.add_arguments(config_parser)

        return parser

    async def run(self, args: List[str] = None) -> int:
        """Main CLI execution method"""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        # Configure logging level
        if parsed_args.verbose:
            self.logger.setLevel(logging.DEBUG)

        # Load configuration
        config = self._load_config(parsed_args.config_file)

        try:
            # Execute command
            if parsed_args.command == 'review':
                return await ReviewCommand(self.controller, self.logger).execute(parsed_args, config)
            elif parsed_args.command == 'report':
                return await ReportCommand(self.controller, self.logger).execute(parsed_args, config)
            elif parsed_args.command == 'status':
                return await StatusCommand(self.controller, self.logger).execute(parsed_args, config)
            elif parsed_args.command == 'config':
                return await ConfigCommand(self.controller, self.logger).execute(parsed_args, config)
            else:
                parser.print_help()
                return 1

        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            if parsed_args.verbose:
                import traceback
                traceback.print_exc()
            return 1

    def _load_config(self, config_file: Path) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            "project_path": str(Path.cwd()),
            "output_directory": "reports",
            "include_patterns": ["*.py", "*.yaml", "*.json", "*.md"],
            "exclude_patterns": ["*.pyc", "__pycache__/*", ".git/*"],
            "component_weights": {
                "infrastructure": 0.35,
                "monetization": 0.25,
                "automation": 0.20,
                "documentation": 0.10,
                "testing": 0.05,
                "security": 0.05
            },
            "service_endpoints": {
                "phoenix_core": "http://localhost:8080/health",
                "nca_toolkit": "http://localhost:8081/health",
                "n8n": "http://localhost:5678",
                "windmill": "http://localhost:8000",
                "prometheus": "http://localhost:9090",
                "grafana": "http://localhost:3000"
            }
        }

        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                default_config.update(user_config)
                self.logger.debug(f"Loaded configuration from {config_file}")
            except Exception as e:
                self.logger.warning(
                    f"Failed to load config file {config_file}: {e}")

        return default_config


def main():
    """Main entry point for the CLI application"""
    cli = PhoenixReviewCLI()
    try:
        exit_code = asyncio.run(cli.run())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        sys.exit(130)


if __name__ == '__main__':
    main()
