"""
CLI command implementations for Phoenix Hydra System Review Tool

This module contains the implementation of all CLI commands including
review, report, status, and configuration management.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging
from datetime import datetime

from ..models.data_models import ComponentCategory, Priority, TaskStatus
from ..core.system_controller import SystemReviewController


class BaseCommand:
    """Base class for all CLI commands"""

    def __init__(self, controller: SystemReviewController, logger: logging.Logger):
        self.controller = controller
        self.logger = logger

    async def execute(self, args: argparse.Namespace, config: Dict[str, Any]) -> int:
        """Execute the command - to be implemented by subclasses"""
        raise NotImplementedError

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        """Add command-specific arguments - to be implemented by subclasses"""
        raise NotImplementedError


class ReviewCommand(BaseCommand):
    """Execute comprehensive system review"""

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            '--project-path',
            type=Path,
            help='Path to Phoenix Hydra project (default: current directory)'
        )

        parser.add_argument(
            '--output-dir', '-o',
            type=Path,
            default=Path('reports'),
            help='Output directory for reports (default: reports/)'
        )

        parser.add_argument(
            '--format', '-f',
            choices=['json', 'yaml', 'markdown', 'html'],
            default='markdown',
            help='Output format (default: markdown)'
        )

        parser.add_argument(
            '--components', '-c',
            nargs='+',
            choices=[cat.value for cat in ComponentCategory],
            help='Specific components to review (default: all)'
        )

        parser.add_argument(
            '--skip-services',
            action='store_true',
            help='Skip service health checks'
        )

        parser.add_argument(
            '--parallel',
            type=int,
            default=4,
            help='Number of parallel analysis tasks (default: 4)'
        )

    async def execute(self, args: argparse.Namespace, config: Dict[str, Any]) -> int:
        """Execute comprehensive system review"""
        self.logger.info("Starting Phoenix Hydra system review...")

        # Determine project path
        project_path = args.project_path or Path(config['project_path'])
        if not project_path.exists():
            self.logger.error(f"Project path does not exist: {project_path}")
            return 1

        # Create output directory
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Configure controller
            await self.controller.configure(
                project_path=project_path,
                config=config,
                skip_services=args.skip_services,
                parallel_tasks=args.parallel
            )

            # Filter components if specified
            components = None
            if args.components:
                components = [ComponentCategory(comp)
                              for comp in args.components]

            # Execute review phases
            self.logger.info(
                "Phase 1: Discovery - Scanning project structure...")
            discovery_results = await self.controller.discover_components(
                include_components=components
            )

            self.logger.info("Phase 2: Analysis - Evaluating components...")
            analysis_results = await self.controller.analyze_components(
                discovery_results
            )

            self.logger.info("Phase 3: Assessment - Calculating completion...")
            assessment_results = await self.controller.assess_completion(
                analysis_results
            )

            self.logger.info("Phase 4: Reporting - Generating outputs...")
            reports = await self.controller.generate_reports(
                assessment_results,
                output_format=args.format
            )

            # Save reports
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            for report_type, content in reports.items():
                filename = f"phoenix_review_{report_type}_{timestamp}.{args.format}"
                output_file = output_dir / filename

                if args.format == 'json':
                    with open(output_file, 'w') as f:
                        json.dump(content, f, indent=2, default=str)
                else:
                    with open(output_file, 'w') as f:
                        f.write(content)

                self.logger.info(
                    f"Generated {report_type} report: {output_file}")

            # Print summary
            completion_percentage = assessment_results.get(
                'overall_completion', 0)
            total_gaps = len(assessment_results.get('gaps', []))

            print(f"\n🚀 Phoenix Hydra System Review Complete!")
            print(f"📊 Overall Completion: {completion_percentage:.1f}%")
            print(f"🔍 Gaps Identified: {total_gaps}")
            print(f"📁 Reports saved to: {output_dir}")

            return 0

        except Exception as e:
            self.logger.error(f"Review failed: {e}")
            return 1


class ReportCommand(BaseCommand):
    """Generate specific reports"""

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            '--type', '-t',
            choices=['todo', 'status', 'gaps',
                     'completion', 'recommendations'],
            required=True,
            help='Type of report to generate'
        )

        parser.add_argument(
            '--format', '-f',
            choices=['json', 'yaml', 'markdown', 'csv'],
            default='markdown',
            help='Output format (default: markdown)'
        )

        parser.add_argument(
            '--priority', '-p',
            choices=[p.value for p in Priority],
            help='Filter by priority level'
        )

        parser.add_argument(
            '--category', '-c',
            choices=[cat.value for cat in ComponentCategory],
            help='Filter by component category'
        )

        parser.add_argument(
            '--output', '-o',
            type=Path,
            help='Output file path (default: stdout)'
        )

    async def execute(self, args: argparse.Namespace, config: Dict[str, Any]) -> int:
        """Generate specific report"""
        self.logger.info(f"Generating {args.type} report...")

        try:
            # Load existing assessment results if available
            results_file = Path('reports/latest_assessment.json')
            if not results_file.exists():
                self.logger.error(
                    "No assessment results found. Run 'phoenix-review review' first.")
                return 1

            with open(results_file, 'r') as f:
                assessment_results = json.load(f)

            # Generate specific report
            report_content = await self._generate_specific_report(
                args.type,
                assessment_results,
                args.format,
                priority_filter=args.priority,
                category_filter=args.category
            )

            # Output report
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(report_content)
                self.logger.info(f"Report saved to: {args.output}")
            else:
                print(report_content)

            return 0

        except Exception as e:
            self.logger.error(f"Report generation failed: {e}")
            return 1

    async def _generate_specific_report(
        self,
        report_type: str,
        assessment_results: Dict[str, Any],
        format_type: str,
        priority_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> str:
        """Generate specific report content"""

        if report_type == 'todo':
            return await self._generate_todo_report(
                assessment_results, format_type, priority_filter, category_filter
            )
        elif report_type == 'status':
            return await self._generate_status_report(
                assessment_results, format_type, category_filter
            )
        elif report_type == 'gaps':
            return await self._generate_gaps_report(
                assessment_results, format_type, priority_filter, category_filter
            )
        elif report_type == 'completion':
            return await self._generate_completion_report(
                assessment_results, format_type, category_filter
            )
        elif report_type == 'recommendations':
            return await self._generate_recommendations_report(
                assessment_results, format_type
            )
        else:
            raise ValueError(f"Unknown report type: {report_type}")

    async def _generate_todo_report(
        self, results: Dict[str, Any], format_type: str,
        priority_filter: Optional[str], category_filter: Optional[str]
    ) -> str:
        """Generate TODO checklist report"""
        gaps = results.get('gaps', [])

        # Apply filters
        if priority_filter:
            gaps = [g for g in gaps if g.get('priority') == priority_filter]
        if category_filter:
            gaps = [g for g in gaps if g.get('category') == category_filter]

        if format_type == 'json':
            return json.dumps(gaps, indent=2)
        elif format_type == 'markdown':
            content = "# Phoenix Hydra TODO Checklist\n\n"
            for gap in gaps:
                priority_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(
                    gap.get('priority', 'medium'), "⚪")
                content += f"- [ ] {priority_emoji} **{gap.get('title', 'Unknown')}**\n"
                content += f"  - Category: {gap.get('category', 'Unknown')}\n"
                content += f"  - Effort: {gap.get('effort_hours', 0)} hours\n"
                content += f"  - Description: {gap.get('description', 'No description')}\n\n"
            return content
        else:
            return str(gaps)


class StatusCommand(BaseCommand):
    """Show current system status"""

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            '--components', '-c',
            nargs='+',
            choices=[cat.value for cat in ComponentCategory],
            help='Show status for specific components only'
        )

        parser.add_argument(
            '--services',
            action='store_true',
            help='Include service health checks'
        )

        parser.add_argument(
            '--format', '-f',
            choices=['table', 'json', 'yaml'],
            default='table',
            help='Output format (default: table)'
        )

    async def execute(self, args: argparse.Namespace, config: Dict[str, Any]) -> int:
        """Show current system status"""
        self.logger.info("Checking Phoenix Hydra system status...")

        try:
            # Quick status check
            status_results = await self.controller.get_system_status(
                include_services=args.services,
                components=args.components
            )

            if args.format == 'json':
                print(json.dumps(status_results, indent=2, default=str))
            elif args.format == 'yaml':
                import yaml
                print(yaml.dump(status_results, default_flow_style=False))
            else:
                self._print_status_table(status_results)

            return 0

        except Exception as e:
            self.logger.error(f"Status check failed: {e}")
            return 1

    def _print_status_table(self, status_results: Dict[str, Any]):
        """Print status in table format"""
        print("\n🚀 Phoenix Hydra System Status")
        print("=" * 50)

        for category, components in status_results.get('components', {}).items():
            print(f"\n📁 {category.upper()}")
            print("-" * 30)

            for component, status in components.items():
                status_emoji = "✅" if status.get('healthy', False) else "❌"
                completion = status.get('completion_percentage', 0)
                print(f"  {status_emoji} {component}: {completion:.1f}%")

        if 'services' in status_results:
            print(f"\n🔧 SERVICES")
            print("-" * 30)
            for service, status in status_results['services'].items():
                status_emoji = "✅" if status.get('healthy', False) else "❌"
                print(
                    f"  {status_emoji} {service}: {status.get('status', 'Unknown')}")


class ConfigCommand(BaseCommand):
    """Manage configuration settings"""

    @staticmethod
    def add_arguments(parser: argparse.ArgumentParser):
        parser.add_argument(
            '--show',
            action='store_true',
            help='Show current configuration'
        )

        parser.add_argument(
            '--set',
            nargs=2,
            metavar=('KEY', 'VALUE'),
            help='Set configuration value'
        )

        parser.add_argument(
            '--reset',
            action='store_true',
            help='Reset to default configuration'
        )

    async def execute(self, args: argparse.Namespace, config: Dict[str, Any]) -> int:
        """Manage configuration"""
        config_file = Path('phoenix-review.json')

        try:
            if args.show:
                print(json.dumps(config, indent=2))
                return 0

            elif args.set:
                key, value = args.set
                # Try to parse value as JSON for complex types
                try:
                    parsed_value = json.loads(value)
                except json.JSONDecodeError:
                    parsed_value = value

                config[key] = parsed_value

                with open(config_file, 'w') as f:
                    json.dump(config, f, indent=2)

                self.logger.info(f"Set {key} = {parsed_value}")
                return 0

            elif args.reset:
                if config_file.exists():
                    config_file.unlink()
                self.logger.info("Configuration reset to defaults")
                return 0

            else:
                self.logger.error(
                    "No action specified. Use --show, --set, or --reset")
                return 1

        except Exception as e:
            self.logger.error(f"Configuration operation failed: {e}")
            return 1
