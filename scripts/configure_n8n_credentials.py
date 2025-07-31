#!/usr/bin/env python3
"""
Quick script to configure n8n credentials for Phoenix Hydra
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phoenix_system_review.core.secrets_manager import SecretsManager
from phoenix_system_review.core.logging_system import setup_logging, LogLevel


def main():
    """Configure n8n credentials"""
    print("🔐 Configuring n8n credentials for Phoenix Hydra")
    print("=" * 50)
    
    # Setup logging
    logger = setup_logging(log_level=LogLevel.INFO, enable_console=True, enable_file=False)
    
    # Generate a master key if not provided
    master_key = os.getenv("PHOENIX_MASTER_KEY")
    if not master_key:
        import secrets
        import string
        
        # Generate a strong master key
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        master_key = ''.join(secrets.choice(alphabet) for _ in range(32))
        
        print(f"🔑 Generated master key: {master_key}")
        print("⚠️  IMPORTANT: Set this as PHOENIX_MASTER_KEY environment variable!")
        print(f"   For PowerShell: $env:PHOENIX_MASTER_KEY = '{master_key}'")
        print(f"   For CMD: set PHOENIX_MASTER_KEY={master_key}")
        print()
        
        # Set for current session
        os.environ["PHOENIX_MASTER_KEY"] = master_key
    
    try:
        # Initialize secrets manager
        secrets_manager = SecretsManager(master_key=master_key)
        
        # Configure n8n credentials
        n8n_user = "ykan.prod@gmail.com"
        n8n_password = "Rivotrip7$"
        
        print("📧 Setting n8n credentials...")
        secrets_manager.set_secret("n8n_user", n8n_user, save_to_file=False)
        secrets_manager.set_secret("n8n_password", n8n_password, save_to_file=False)
        
        # Generate some default security keys
        import secrets as sec
        import string
        
        jwt_secret = ''.join(sec.choice(string.ascii_letters + string.digits) for _ in range(64))
        encryption_key = ''.join(sec.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(32))
        
        secrets_manager.set_secret("jwt_secret", jwt_secret, save_to_file=False)
        secrets_manager.set_secret("encryption_key", encryption_key, save_to_file=False)
        
        # Save all secrets
        secrets_manager._save_secrets()
        
        print("✅ n8n credentials configured successfully!")
        
        # Test the configuration
        print("\n🧪 Testing configuration...")
        n8n_creds = secrets_manager.get_n8n_credentials()
        print(f"✅ n8n user: {n8n_creds['user']}")
        print(f"✅ n8n password: {'*' * len(n8n_creds['password'])}")
        
        # Validate all secrets
        validation = secrets_manager.validate_secrets()
        print(f"\n📊 Secrets validation:")
        print(f"   Total secrets: {validation['total_secrets']}")
        print(f"   Configured: {validation['configured_secrets']}")
        
        if validation["valid"]:
            print("🎉 All required secrets are configured!")
        else:
            print("⚠️  Some required secrets are missing:")
            for missing in validation["missing_required"]:
                print(f"   - {missing}")
        
        # Export environment file
        print("\n📄 Exporting environment file...")
        secrets_manager.export_environment_file(".env.secrets")
        print("✅ Environment file exported to .env.secrets")
        
        print("\n🎯 Next Steps:")
        print("1. Set the PHOENIX_MASTER_KEY environment variable permanently")
        print("2. Add .env.secrets to your .gitignore (already done)")
        print("3. Start Phoenix Hydra services:")
        print("   podman-compose -f infra/podman/compose.secrets.yaml up -d")
        print("4. Access n8n at: http://localhost:5678")
        print(f"   Username: {n8n_user}")
        print("   Password: [use the password you provided]")
        
    except Exception as e:
        logger.error(f"Configuration failed: {e}")
        print(f"\n❌ Configuration failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()