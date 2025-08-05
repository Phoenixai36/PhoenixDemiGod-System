#!/usr/bin/env python3
"""
Command-line interface for Phoenix Hydra security management.
Provides basic commands to test and interact with the security system.
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Add the scripts directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from security.base.exceptions import SecurityError
from security.security_manager import create_security_manager


async def cmd_status(args):
    """Show security system status."""
    try:
        manager = await create_security_manager()
        status = await manager.get_security_status()
        
        print("Phoenix Hydra Security Status:")
        print(f"  Initialized: {status['initialized']}")
        print(f"  Config Loaded: {status['config_loaded']}")
        print("  Components:")
        for component, loaded in status['components'].items():
            print(f"    {component}: {'✓' if loaded else '✗'}")
        print(f"  Last Updated: {status['timestamp']}")
        
    except SecurityError as e:
        print(f"Security Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1
    
    return 0


async def cmd_health(args):
    """Perform health check of security system."""
    try:
        manager = await create_security_manager()
        health = await manager.health_check()
        
        print(f"Security System Health: {health['status'].upper()}")
        print("Health Checks:")
        for check, result in health['checks'].items():
            status_icon = "✓" if result == "ok" else "✗" if result == "error" else "?"
            print(f"  {check}: {status_icon} {result}")
        
        if 'error' in health:
            print(f"Error Details: {health['error']}")
        
        return 0 if health['status'] == "healthy" else 1
        
    except SecurityError as e:
        print(f"Security Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1


async def cmd_config(args):
    """Show or validate security configuration."""
    try:
        manager = await create_security_manager()
        
        if args.validate:
            issues = manager.config.validate()
            if issues:
                print("Configuration Issues:")
                for issue in issues:
                    print(f"  - {issue}")
                return 1
            else:
                print("Configuration is valid ✓")
                return 0
        else:
            # Show configuration summary
            config = manager.config
            print("Security Configuration Summary:")
            print(f"  Environment: {config.environment}")
            print(f"  Debug Mode: {config.debug_mode}")
            print(f"  Vulnerability DB: {config.scanner.vulnerability_db_path}")
            print(f"  Audit Logs: {config.audit.audit_log_path}")
            print(f"  Auto Security Updates: {config.update_manager.auto_apply_security_patches}")
            print(f"  Offline Compatibility Required: {config.validator.require_offline_compatibility}")
            print(f"  Privacy Compliance Required: {config.validator.require_privacy_compliance}")
            
    except SecurityError as e:
        print(f"Security Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1
    
    return 0


async def cmd_init(args):
    """Initialize security infrastructure."""
    try:
        print("Initializing Phoenix Hydra Security Infrastructure...")
        manager = await create_security_manager()
        
        print("✓ Security manager initialized")
        print("✓ Configuration loaded")
        print("✓ Directories created")
        print("✓ Components prepared")
        
        # Show next steps
        print("\nNext Steps:")
        print("  1. Run 'python scripts/security/cli.py status' to check system status")
        print("  2. Run 'python scripts/security/cli.py health' to perform health check")
        print("  3. Implement security scanner (Task 2.1)")
        print("  4. Implement dependency validator (Task 3.1)")
        
        return 0
        
    except SecurityError as e:
        print(f"Security Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Phoenix Hydra Security Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/security/cli.py init          # Initialize security infrastructure
  python scripts/security/cli.py status       # Show security system status
  python scripts/security/cli.py health       # Perform health check
  python scripts/security/cli.py config       # Show configuration summary
  python scripts/security/cli.py config --validate  # Validate configuration
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize security infrastructure')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show security system status')
    
    # Health command
    health_parser = subparsers.add_parser('health', help='Perform health check')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Show or validate configuration')
    config_parser.add_argument('--validate', action='store_true', help='Validate configuration')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Map commands to functions
    commands = {
        'init': cmd_init,
        'status': cmd_status,
        'health': cmd_health,
        'config': cmd_config
    }
    
    if args.command in commands:
        return asyncio.run(commands[args.command](args))
    else:
        print(f"Unknown command: {args.command}")
        return 1


if __name__ == "__main__":
    sys.exit(main())