#!/usr/bin/env python3
"""
Validate Phoenix Hydra configuration
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phoenix_system_review.core.config_validator import ConfigValidator


def main():
    """Main validation function"""
    print("🔍 Phoenix Hydra Configuration Validation")
    print("=" * 50)
    
    # Set master key if available
    master_key = os.getenv("PHOENIX_MASTER_KEY")
    if not master_key:
        print("⚠️  PHOENIX_MASTER_KEY not found in environment")
        print("   Please set it first: $env:PHOENIX_MASTER_KEY = 'your-master-key'")
        return 1
    
    try:
        validator = ConfigValidator()
        summary = validator.validate_all()
        validator.print_summary(summary)
        
        return 0 if summary["overall_status"] == "PASS" else 1
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())