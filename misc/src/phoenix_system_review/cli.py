#!/usr/bin/env python3
"""
Phoenix Hydra System Review CLI

Command-line interface for executing comprehensive system reviews,
generating reports, and managing the Phoenix Hydra system analysis.
"""

import argparse
import sys
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from .core.system_review_engine import SystemReviewEngine
from .models.data_models import Priority
from .reporting.report_generator import ReportGenerator


class PhoenixSystemReviewCLI:
    """
    Command-line interface for Phoenix Hydra system review operations.
    """

    def __init__(self):
        """Initialize the CLI application."""
        self.logger = self._setup_logging()
        self.engine = None
        self.report_generator = None

    def _setup_logging(self, level: str = "INFO") -> logging.Logger:
        """Set up logging configuration."""
        logging.basicConfig(
            level=getattr(logging, level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        return logging.getLogger(__name__)

    def create_parser(self) -> argparse.ArgumentParser:
        """Create and configure the argument parser."""
        parser = argparse.ArgumentParser(
            prog='phoenix-review',
            description='Phoenix Hydra System Review CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  phoenix-review analyze /path/to/phoenix-hydra
  phoenix-review report --format json --output report.json
  phoenix-review status --component podman
  phoenix-review todo --priority high --format markdown
  phoenix-review health-check --services all
            """
        )

        # Global options
        parser.add_argument(
            '--project-root', '-p',
            type=str,
            default='.',
            help='Path to Phoenix Hydra project root (default: current directory)'
        )

        parser.add_argument(
            '--config', '-c',
            type=str,
            help='Path to configuration file'
        )

        parser.add_argument(
            '--verbose', '-v',
            action='count',
            default=0,
            help='Increase verbosity (use -v, -vv, or -vvv)'
        )

        parser.add_argument(
            '--quiet', '-q',
            action='store_true',
            help='Suppress all output except errors'
        )

        parser.add_argument(
            '--output', '-o',
            type=str,
            help='Output file path (default: stdout)'
        )

        parser.add_argument(
            '--format', '-f',
            choices=['json', 'yaml', 'markdown', 'text', 'html'],
            default='text',
            help='Output format (default: text)'
        )

        # Subcommands
        subparsers = parser.add_subparsers(
            dest='command',
            help='Available commands',
            metavar='COMMAND'
        )

        # Analyze command
        analyze_parser = subparsers.add_parser(
            'analyze',
            help='Run comprehensive system analysis'
        )
        analyze_parser.add_argument(
            'path',
            nargs='?',
            default='.',
            help='Path to analyze (default: current directory)'
        )
        analyze_parser.add_argument(
            '--components',
            nargs='+',
            help='Specific components to analyze (e.g., podman, n8n, windmill)'
        )
        analyze_parser.add_argument(
            '--skip-tests',
            action='store_true',
            help='Skip running integration tests during analysis'
        )
        analyze_parser.add_argument(
            '--deep-scan',
            action='store_true',
            help='Perform deep analysis including code quality checks'
        )

        # Report command
        report_parser = subparsers.add_parser(
            'report',
            help='Generate system review reports'
        )
        report_parser.add_argument(
            '--type',
            choices=['summary', 'detailed', 'executive', 'technical'],
            default='summary',
            help='Type of report to generate (default: summary)'
        )
        report_parser.add_argument(
            '--include-recommendations',
            action='store_true',
            help='Include recommendations in the report'
        )
        report_parser.add_argument(
            '--include-metrics',
            action='store_true',
            help='Include performance metrics in the report'
        )

        # Status command
        status_parser = subparsers.add_parser(
            'status',
            help='Show system status and completion percentages'
        )
        status_parser.add_argument(
            '--component',
            help='Show status for specific component'
        )
        status_parser.add_argument(
            '--summary',
            action='store_true',
            help='Show only summary information'
        )

        # TODO command
        todo_parser = subparsers.add_parser(
            'todo',
            help='Generate TODO checklist from identified gaps'
        )
        todo_parser.add_argument(
            '--priority',
            choices=['critical', 'high', 'medium', 'low', 'all'],
            default='all',
            help='Filter by priority level (default: all)'
        )
        todo_parser.add_argument(
            '--component',
            help='Filter by component'
        )
        todo_parser.add_argument(
            '--assignable',
            action='store_true',
            help='Only show tasks that can be immediately worked on'
        )

        # Health check command
        health_parser = subparsers.add_parser(
            'health-check',
            help='Check health of Phoenix Hydra services'
        )
        health_parser.add_argument(
            '--services',
            nargs='+',
            default=['all'],
            help='Services to check (podman, n8n, windmill, phoenix-core, nca-toolkit, all)'
        )
        health_parser.add_argument(
            '--timeout',
            type=int,
            default=30,
            help='Timeout for health checks in seconds (default: 30)'
        )

        # Validate command
        validate_parser = subparsers.add_parser(
            'validate',
            help='Validate system configuration and setup'
        )
        validate_parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix validation issues automatically'
        )
        validate_parser.add_argument(
            '--strict',
            action='store_true',
            help='Use strict validation rules'
        )

        # Init command
        init_parser = subparsers.add_parser(
            'init',
            help='Initialize system review configuration'
        )
        init_parser.add_argument(
            '--template',
            choices=['basic', 'advanced', 'enterprise'],
            default='basic',
            help='Configuration template to use (default: basic)'
        )

        return parser

    def _initialize_engine(self, project_root: str, config_path: Optional[str] = None) -> None:
        """Initialize the system review engine."""
        try:
            self.engine = SystemReviewEngine(project_root)
            self.report_generator = ReportGenerator()

            if config_path and Path(config_path).exists():
                self.logger.info(f"Loading configuration from {config_path}")
                # Load custom configuration if provided
                # This would be implemented based on the configuration system

        except Exception as e:
            self.logger.error(
                f"Failed to initialize system review engine: {e}")
            sys.exit(1)

    def _set_log_level(self, verbosity: int, quiet: bool) -> None:
        """Set logging level based on verbosity flags."""
        if quiet:
            level = logging.ERROR
        elif verbosity >= 3:
            level = logging.DEBUG
        elif verbosity == 2:
            level = logging.INFO
        elif verbosity == 1:
            level = logging.WARNING
        else:
            level = logging.ERROR

        logging.getLogger().setLevel(level)

    def _output_result(self, data: Any, format_type: str, output_path: Optional[str] = None) -> None:
        """Output result in the specified format."""
        try:
            if format_type == 'json':
                content = json.dumps(data, indent=2, default=str)
            elif format_type == 'yaml':
                content = yaml.dump(data, default_flow_style=False)
            elif format_type == 'markdown':
                content = self._format_as_markdown(data)
            elif format_type == 'html':
                content = self._format_as_html(data)
            else:  # text
                content = self._format_as_text(data)

            if output_path:
                Path(output_path).write_text(content, encoding='utf-8')
                self.logger.info(f"Output written to {output_path}")
            else:
                print(content)

        except Exception as e:
            self.logger.error(f"Failed to output result: {e}")
            sys.exit(1)

    def _format_as_markdown(self, data: Any) -> str:
        """Format data as Markdown."""
        if isinstance(data, dict):
            lines = ["# Phoenix Hydra System Review Report", ""]

            if 'timestamp' in data:
                lines.extend([f"**Generated:** {data['timestamp']}", ""])

            if 'summary' in data:
                lines.extend(["## Summary", "", str(data['summary']), ""])

            if 'components' in data:
                lines.extend(["## Components", ""])
                for component, info in data['components'].items():
                    lines.append(f"### {component.title()}")
                    if isinstance(info, dict):
                        for key, value in info.items():
                            lines.append(f"- **{key.title()}:** {value}")
                    lines.append("")

            return "\n".join(lines)

        return str(data)

    def _format_as_html(self, data: Any) -> str:
        """Format data as HTML."""
        html = """<!DOCTYPE html>
<html>
<head>
    <title>Phoenix Hydra System Review Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .header { color: #2c3e50; border-bottom: 2px solid #3498db; }
        .component { margin: 20px 0; padding: 15px; border-left: 4px solid #3498db; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #ecf0f1; }
        .critical { border-left-color: #e74c3c; }
        .warning { border-left-color: #f39c12; }
        .success { border-left-color: #27ae60; }
    </style>
</head>
<body>
    <h1 class="header">Phoenix Hydra System Review Report</h1>
"""

        if isinstance(data, dict):
            if 'timestamp' in data:
                html += f"<p><strong>Generated:</strong> {data['timestamp']}</p>"

            if 'summary' in data:
                html += f"<h2>Summary</h2><p>{data['summary']}</p>"

            if 'components' in data:
                html += "<h2>Components</h2>"
                for component, info in data['components'].items():
                    html += f'<div class="component"><h3>{component.title()}</h3>'
                    if isinstance(info, dict):
                        for key, value in info.items():
                            html += f'<div class="metric"><strong>{key.title()}:</strong> {value}</div>'
                    html += "</div>"

        html += "</body></html>"
        return html

    def _format_as_text(self, data: Any) -> str:
        """Format data as plain text."""
        if isinstance(data, dict):
            lines = ["Phoenix Hydra System Review Report", "=" * 40, ""]

            if 'timestamp' in data:
                lines.extend([f"Generated: {data['timestamp']}", ""])

            if 'summary' in data:
                lines.extend(["Summary:", "-" * 8, str(data['summary']), ""])

            if 'components' in data:
                lines.extend(["Components:", "-" * 11, ""])
                for component, info in data['components'].items():
                    lines.append(f"{component.upper()}:")
                    if isinstance(info, dict):
                        for key, value in info.items():
                            lines.append(f"  {key.title()}: {value}")
                    lines.append("")

            return "\n".join(lines)

        return str(data)

    def cmd_analyze(self, args: argparse.Namespace) -> None:
        """Execute the analyze command."""
        self.logger.info(f"Starting system analysis of {args.path}")

        try:
            # Run comprehensive analysis
            result = self.engine.run_comprehensive_review()

            # Filter by components if specified
            if args.components:
                filtered_result = self._filter_by_components(
                    result, args.components)
                result = filtered_result

            # Format output data
            output_data = {
                'timestamp': datetime.now().isoformat(),
                'project_path': str(Path(args.path).absolute()),
                'analysis_type': 'comprehensive' if not args.components else 'filtered',
                'components_analyzed': args.components or 'all',
                'summary': {
                    'overall_completion': result.overall_completion_percentage,
                    'total_components': len(result.component_results),
                    'total_issues': sum(len(comp.issues) for comp in result.component_results),
                    'critical_issues': sum(
                        len([i for i in comp.issues if i.severity == Priority.CRITICAL])
                        for comp in result.component_results
                    )
                },
                'components': {
                    comp.component.name: {
                        'completion_percentage': comp.completion_percentage,
                        'quality_score': comp.quality_score,
                        'status': comp.component.status.value,
                        'issues_count': len(comp.issues),
                        'criteria_met': len(comp.criteria_met),
                        'criteria_missing': len(comp.criteria_missing)
                    }
                    for comp in result.component_results
                }
            }

            self._output_result(output_data, args.format, args.output)

        except Exception as e:
            self.logger.error(f"Analysis failed: {e}")
            sys.exit(1)

    def cmd_report(self, args: argparse.Namespace) -> None:
        """Execute the report command."""
        self.logger.info(f"Generating {args.type} report")

        try:
            # Generate report based on type
            if args.type == 'summary':
                report_data = self.report_generator.generate_summary_report()
            elif args.type == 'detailed':
                report_data = self.report_generator.generate_detailed_report()
            elif args.type == 'executive':
                report_data = self.report_generator.generate_executive_summary()
            elif args.type == 'technical':
                report_data = self.report_generator.generate_technical_report()
            else:
                report_data = self.report_generator.generate_summary_report()

            # Add optional sections
            if args.include_recommendations:
                recommendations = self.engine.get_recommendations()
                report_data['recommendations'] = recommendations

            if args.include_metrics:
                metrics = self.engine.get_performance_metrics()
                report_data['metrics'] = metrics

            report_data['timestamp'] = datetime.now().isoformat()
            report_data['report_type'] = args.type

            self._output_result(report_data, args.format, args.output)

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            sys.exit(1)

    def cmd_status(self, args: argparse.Namespace) -> None:
        """Execute the status command."""
        self.logger.info("Checking system status")

        try:
            status_data = self.engine.get_system_status()

            if args.component:
                # Filter for specific component
                component_status = status_data.get(
                    'components', {}).get(args.component)
                if component_status:
                    status_data = {
                        'component': args.component,
                        'status': component_status,
                        'timestamp': datetime.now().isoformat()
                    }
                else:
                    self.logger.error(
                        f"Component '{args.component}' not found")
                    sys.exit(1)

            if args.summary:
                # Show only summary information
                summary_data = {
                    'overall_health': status_data.get('overall_health', 'unknown'),
                    'completion_percentage': status_data.get('completion_percentage', 0),
                    'active_issues': status_data.get('active_issues', 0),
                    'timestamp': datetime.now().isoformat()
                }
                status_data = summary_data

            self._output_result(status_data, args.format, args.output)

        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            sys.exit(1)

    def cmd_todo(self, args: argparse.Namespace) -> None:
        """Execute the todo command."""
        self.logger.info("Generating TODO checklist")

        try:
            todo_items = self.engine.generate_todo_list()

            # Filter by priority
            if args.priority != 'all':
                priority_filter = Priority[args.priority.upper()]
                todo_items = [
                    item for item in todo_items if item.priority == priority_filter]

            # Filter by component
            if args.component:
                todo_items = [
                    item for item in todo_items if item.component == args.component]

            # Filter for assignable tasks only
            if args.assignable:
                todo_items = [
                    item for item in todo_items if item.is_actionable]

            todo_data = {
                'timestamp': datetime.now().isoformat(),
                'filters': {
                    'priority': args.priority,
                    'component': args.component,
                    'assignable_only': args.assignable
                },
                'total_items': len(todo_items),
                'items': [
                    {
                        'id': item.id,
                        'title': item.title,
                        'description': item.description,
                        'priority': item.priority.value,
                        'component': item.component,
                        'effort_estimate': item.effort_estimate,
                        'dependencies': item.dependencies,
                        'is_actionable': item.is_actionable
                    }
                    for item in todo_items
                ]
            }

            self._output_result(todo_data, args.format, args.output)

        except Exception as e:
            self.logger.error(f"TODO generation failed: {e}")
            sys.exit(1)

    def cmd_health_check(self, args: argparse.Namespace) -> None:
        """Execute the health-check command."""
        self.logger.info(
            f"Checking health of services: {', '.join(args.services)}")

        try:
            health_results = {}

            if 'all' in args.services:
                services_to_check = ['podman', 'n8n',
                                     'windmill', 'phoenix-core', 'nca-toolkit']
            else:
                services_to_check = args.services

            for service in services_to_check:
                self.logger.debug(f"Checking {service} health")
                health_status = self.engine.check_service_health(
                    service, timeout=args.timeout)
                health_results[service] = health_status

            health_data = {
                'timestamp': datetime.now().isoformat(),
                'services_checked': services_to_check,
                'timeout': args.timeout,
                'results': health_results,
                'overall_health': 'healthy' if all(
                    result.get('healthy', False) for result in health_results.values()
                ) else 'unhealthy'
            }

            self._output_result(health_data, args.format, args.output)

        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            sys.exit(1)

    def cmd_validate(self, args: argparse.Namespace) -> None:
        """Execute the validate command."""
        self.logger.info("Validating system configuration")

        try:
            validation_results = self.engine.validate_system_configuration(
                strict=args.strict,
                auto_fix=args.fix
            )

            validation_data = {
                'timestamp': datetime.now().isoformat(),
                'validation_mode': 'strict' if args.strict else 'standard',
                'auto_fix_enabled': args.fix,
                'results': validation_results,
                'overall_valid': validation_results.get('valid', False)
            }

            self._output_result(validation_data, args.format, args.output)

            if not validation_results.get('valid', False):
                sys.exit(1)

        except Exception as e:
            self.logger.error(f"Validation failed: {e}")
            sys.exit(1)

    def cmd_init(self, args: argparse.Namespace) -> None:
        """Execute the init command."""
        self.logger.info(
            f"Initializing system review configuration with {args.template} template")

        try:
            config_path = Path('.phoenix-review.yaml')

            if config_path.exists():
                response = input(
                    f"Configuration file {config_path} already exists. Overwrite? (y/N): ")
                if response.lower() != 'y':
                    self.logger.info("Initialization cancelled")
                    return

            # Create configuration based on template
            config_data = self._create_config_template(args.template)

            with open(config_path, 'w') as f:
                yaml.dump(config_data, f, default_flow_style=False)

            self.logger.info(f"Configuration initialized at {config_path}")
            print(f"Configuration file created: {config_path}")
            print("You can now run 'phoenix-review analyze' to start system analysis.")

        except Exception as e:
            self.logger.error(f"Initialization failed: {e}")
            sys.exit(1)

    def _create_config_template(self, template: str) -> Dict[str, Any]:
        """Create configuration template."""
        base_config = {
            'project': {
                'name': 'Phoenix Hydra',
                'version': '1.0.0',
                'description': 'Phoenix Hydra System Review Configuration'
            },
            'analysis': {
                'components': ['podman', 'n8n', 'windmill', 'phoenix-core', 'nca-toolkit'],
                'skip_tests': False,
                'deep_scan': False
            },
            'reporting': {
                'default_format': 'text',
                'include_recommendations': True,
                'include_metrics': False
            },
            'health_checks': {
                'timeout': 30,
                'retry_attempts': 3
            }
        }

        if template == 'advanced':
            base_config.update({
                'analysis': {
                    **base_config['analysis'],
                    'deep_scan': True,
                    'performance_monitoring': True,
                    'security_checks': True
                },
                'reporting': {
                    **base_config['reporting'],
                    'include_metrics': True,
                    'generate_charts': True
                }
            })
        elif template == 'enterprise':
            base_config.update({
                'analysis': {
                    **base_config['analysis'],
                    'deep_scan': True,
                    'performance_monitoring': True,
                    'security_checks': True,
                    'compliance_checks': True
                },
                'reporting': {
                    **base_config['reporting'],
                    'include_metrics': True,
                    'generate_charts': True,
                    'executive_summary': True
                },
                'automation': {
                    'scheduled_reviews': True,
                    'alert_thresholds': {
                        'completion_percentage': 80,
                        'critical_issues': 5
                    }
                }
            })

        return base_config

    def _filter_by_components(self, result: Any, components: List[str]) -> Any:
        """Filter analysis result by specified components."""
        # This would filter the result to only include specified components
        # Implementation depends on the structure of the result object
        return result

    def run(self, argv: Optional[List[str]] = None) -> int:
        """Run the CLI application."""
        parser = self.create_parser()
        args = parser.parse_args(argv)

        # Set up logging
        self._set_log_level(args.verbose, args.quiet)

        # Check if command was provided
        if not args.command:
            parser.print_help()
            return 1

        # Initialize engine for commands that need it
        if args.command not in ['init']:
            self._initialize_engine(args.project_root, args.config)

        # Execute command
        try:
            command_method = getattr(
                self, f'cmd_{args.command.replace("-", "_")}')
            command_method(args)
            return 0
        except AttributeError:
            self.logger.error(f"Unknown command: {args.command}")
            return 1
        except KeyboardInterrupt:
            self.logger.info("Operation cancelled by user")
            return 130
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            return 1


def main():
    """Main entry point for the CLI application."""
    cli = PhoenixSystemReviewCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
