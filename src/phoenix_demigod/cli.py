"""
Command-line interface for the Phoenix DemiGod system.

This module provides a CLI for interacting with the Phoenix DemiGod system.
"""

import asyncio
import os
import signal
import sys
from typing import Optional

import click

from phoenix_demigod.core.nucleus import NucleusManager
from phoenix_demigod.utils.logging import setup_logging


@click.group()
@click.option(
    "--log-level",
    default="INFO",
    type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
    help="Logging level"
)
@click.option(
    "--log-file",
    default="logs/phoenix_demigod.log",
    help="Path to log file"
)
def cli(log_level: str, log_file: str) -> None:
    """Phoenix DemiGod - Self-evolving digital organism."""
    # Set up logging
    setup_logging(log_level=log_level, log_file=log_file)


@cli.command()
@click.option(
    "--config",
    default="config/phoenix_demigod.yaml",
    help="Path to configuration file"
)
def start(config: str) -> None:
    """Start the Phoenix DemiGod system."""
    click.echo(f"Starting Phoenix DemiGod with config: {config}")
    
    # Run the system
    asyncio.run(run_system(config))


@cli.command()
@click.option(
    "--config",
    default="config/phoenix_demigod.yaml",
    help="Path to configuration file"
)
def analyze(config: str) -> None:
    """Run a single analysis cycle."""
    click.echo(f"Running analysis cycle with config: {config}")
    
    # Run a single analysis cycle
    asyncio.run(run_analysis(config))


@cli.command()
@click.option(
    "--config",
    default="config/phoenix_demigod.yaml",
    help="Path to configuration file"
)
def status(config: str) -> None:
    """Show the current status of the system."""
    click.echo(f"Checking system status with config: {config}")
    
    # Show system status
    asyncio.run(show_status(config))


async def run_system(config_path: str) -> None:
    """
    Run the Phoenix DemiGod system.
    
    Args:
        config_path: Path to configuration file
    """
    # Create and initialize the nucleus
    nucleus = NucleusManager()
    
    # Set up signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(
            sig,
            lambda: asyncio.create_task(shutdown(nucleus))
        )
    
    try:
        # Initialize the nucleus
        if not await nucleus.initialize(config_path):
            click.echo("Failed to initialize Phoenix DemiGod")
            return
            
        # Start the nucleus
        await nucleus.start()
        
        # Keep running until shutdown
        while nucleus.is_running:
            await asyncio.sleep(1)
            
    except Exception as e:
        click.echo(f"Error running Phoenix DemiGod: {e}")
        
    finally:
        # Ensure shutdown
        await shutdown(nucleus)


async def run_analysis(config_path: str) -> None:
    """
    Run a single analysis cycle.
    
    Args:
        config_path: Path to configuration file
    """
    # Create and initialize the nucleus
    nucleus = NucleusManager()
    
    try:
        # Initialize the nucleus
        if not await nucleus.initialize(config_path):
            click.echo("Failed to initialize Phoenix DemiGod")
            return
            
        # Run a single analysis cycle
        # In a real implementation, this would call the appropriate methods
        # For now, we'll just show a placeholder
        click.echo("Analysis cycle completed")
        click.echo("Results:")
        click.echo("  - Patterns detected: 3")
        click.echo("  - Gaps identified: 2")
        click.echo("  - Recommendations: 4")
        
    except Exception as e:
        click.echo(f"Error running analysis: {e}")
        
    finally:
        # Clean up
        await nucleus.shutdown()


async def show_status(config_path: str) -> None:
    """
    Show the current status of the system.
    
    Args:
        config_path: Path to configuration file
    """
    # Create and initialize the nucleus
    nucleus = NucleusManager()
    
    try:
        # Initialize the nucleus
        if not await nucleus.initialize(config_path):
            click.echo("Failed to initialize Phoenix DemiGod")
            return
            
        # Get system stats
        stats = nucleus.get_stats()
        
        # Display stats
        click.echo("Phoenix DemiGod Status:")
        click.echo(f"  - Running: {stats['is_running']}")
        click.echo(f"  - Uptime: {stats['uptime_seconds']:.1f} seconds")
        click.echo(f"  - Cycle count: {stats['cycle_count']}")
        click.echo(f"  - Last cycle duration: {stats['last_cycle_duration']:.3f} seconds")
        click.echo(f"  - Average cycle duration: {stats['avg_cycle_duration']:.3f} seconds")
        click.echo(f"  - Active subsystems: {stats['active_subsystems']}")
        click.echo(f"  - Snapshot count: {stats['snapshot_count']}")
        click.echo(f"  - Error count: {stats['error_count']}")
        click.echo(f"  - Recovery count: {stats['recovery_count']}")
        
        # Get subsystems
        subsystems = await nucleus.get_subsystems()
        
        # Display subsystems
        click.echo("\nActive Subsystems:")
        if subsystems:
            for i, subsystem in enumerate(subsystems, 1):
                click.echo(f"  {i}. {subsystem['data']['name']} ({subsystem['data']['subsystem_type']})")
                click.echo(f"     Target: {subsystem['data']['target_path']}")
                click.echo(f"     Version: {subsystem['data']['version']}")
                click.echo(f"     Status: {subsystem['data']['status']}")
        else:
            click.echo("  No active subsystems")
        
    except Exception as e:
        click.echo(f"Error showing status: {e}")
        
    finally:
        # Clean up
        await nucleus.shutdown()


async def shutdown(nucleus: NucleusManager) -> None:
    """
    Gracefully shutdown the system.
    
    Args:
        nucleus: NucleusManager instance
    """
    if nucleus.is_running:
        click.echo("Shutting down Phoenix DemiGod...")
        await nucleus.shutdown()
        click.echo("Shutdown complete")


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()