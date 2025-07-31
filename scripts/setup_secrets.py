#!/usr/bin/env python3
"""
Phoenix Hydra Secrets Setup Script

This script securely configures credentials for the Phoenix Hydra system,
including n8n, database, and other service credentials.
"""

import os
import sys
import getpass
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from phoenix_system_review.core.secrets_manager import SecretsManager, setup_secrets_manager
from phoenix_system_review.core.logging_system import setup_logging, LogLevel


def setup_master_key() -> str:
    """Setup or retrieve master encryption key"""
    print("🔐 Phoenix Hydra Secrets Setup")
    print("=" * 50)
    
    # Check if master key exists in environment
    master_key = os.getenv("PHOENIX_MASTER_KEY")
    
    if not master_key:
        print("\n⚠️  No master key found in environment.")
        print("A master key is required to encrypt stored secrets.")
        
        choice = input("\nWould you like to (g)enerate a new key or (e)nter an existing one? [g/e]: ").lower()
        
        if choice == 'g':
            import secrets
            import string
            
            # Generate a strong master key
            alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
            master_key = ''.join(secrets.choice(alphabet) for _ in range(32))
            
            print(f"\n🔑 Generated master key: {master_key}")
            print("\n⚠️  IMPORTANT: Save this master key securely!")
            print("   You will need it to access your secrets in the future.")
            print("   Consider setting it as PHOENIX_MASTER_KEY environment variable.")
            
            input("\nPress Enter after you've saved the master key...")
            
        else:
            master_key = getpass.getpass("Enter your master key: ")
    
    return master_key


def configure_n8n_credentials(secrets_manager: SecretsManager):
    """Configure n8n credentials"""
    print("\n📧 Configuring n8n Credentials")
    print("-" * 30)
    
    # Set the provided n8n credentials
    n8n_user = "ykan.prod@gmail.com"
    n8n_password = "Rivotrip7$"
    
    print(f"Setting n8n user: {n8n_user}")
    secrets_manager.set_secret("n8n_user", n8n_user, save_to_file=False)
    
    print("Setting n8n password: [HIDDEN]")
    secrets_manager.set_secret("n8n_password", n8n_password, save_to_file=False)
    
    # Optional: Ask for API key
    api_key = input("Enter n8n API key (optional, press Enter to skip): ").strip()
    if api_key:
        secrets_manager.set_secret("n8n_api_key", api_key, save_to_file=False)
    
    print("✅ n8n credentials configured")


def configure_database_credentials(secrets_manager: SecretsManager):
    """Configure database credentials"""
    print("\n🗄️  Configuring Database Credentials")
    print("-" * 35)
    
    # Use defaults or ask for custom values
    db_user = input("PostgreSQL username [phoenix_user]: ").strip() or "phoenix_user"
    secrets_manager.set_secret("postgres_user", db_user, save_to_file=False)
    
    db_password = getpass.getpass("PostgreSQL password: ")
    if db_password:
        secrets_manager.set_secret("postgres_password", db_password, save_to_file=False)
    
    db_name = input("Database name [phoenix_hydra]: ").strip() or "phoenix_hydra"
    secrets_manager.set_secret("postgres_db", db_name, save_to_file=False)
    
    print("✅ Database credentials configured")


def configure_minio_credentials(secrets_manager: SecretsManager):
    """Configure Minio S3 credentials"""
    print("\n🪣 Configuring Minio S3 Credentials")
    print("-" * 33)
    
    access_key = input("Minio access key: ").strip()
    if access_key:
        secrets_manager.set_secret("minio_access_key", access_key, save_to_file=False)
    
    secret_key = getpass.getpass("Minio secret key: ")
    if secret_key:
        secrets_manager.set_secret("minio_secret_key", secret_key, save_to_file=False)
    
    print("✅ Minio credentials configured")


def configure_api_keys(secrets_manager: SecretsManager):
    """Configure API keys"""
    print("\n🔑 Configuring API Keys")
    print("-" * 22)
    
    # OpenAI API Key
    openai_key = getpass.getpass("OpenAI API key (optional): ")
    if openai_key:
        secrets_manager.set_secret("openai_api_key", openai_key, save_to_file=False)
    
    # GitHub Token
    github_token = getpass.getpass("GitHub personal access token (optional): ")
    if github_token:
        secrets_manager.set_secret("github_token", github_token, save_to_file=False)
    
    print("✅ API keys configured")


def configure_security_keys(secrets_manager: SecretsManager):
    """Configure security and encryption keys"""
    print("\n🔒 Configuring Security Keys")
    print("-" * 27)
    
    import secrets
    import string
    
    # Generate JWT secret
    jwt_secret = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(64))
    secrets_manager.set_secret("jwt_secret", jwt_secret, save_to_file=False)
    print("✅ Generated JWT secret")
    
    # Generate encryption key
    encryption_key = ''.join(secrets.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(32))
    secrets_manager.set_secret("encryption_key", encryption_key, save_to_file=False)
    print("✅ Generated encryption key")


def main():
    """Main setup function"""
    # Setup logging
    logger = setup_logging(log_level=LogLevel.INFO, enable_console=True, enable_file=False)
    
    try:
        # Get master key
        master_key = setup_master_key()
        
        # Initialize secrets manager
        secrets_manager = setup_secrets_manager(master_key=master_key)
        
        print("\n🚀 Starting Phoenix Hydra secrets configuration...")
        
        # Configure different credential types
        configure_n8n_credentials(secrets_manager)
        
        # Ask if user wants to configure other services
        if input("\nConfigure database credentials? [y/N]: ").lower().startswith('y'):
            configure_database_credentials(secrets_manager)
        
        if input("\nConfigure Minio S3 credentials? [y/N]: ").lower().startswith('y'):
            configure_minio_credentials(secrets_manager)
        
        if input("\nConfigure API keys? [y/N]: ").lower().startswith('y'):
            configure_api_keys(secrets_manager)
        
        # Always configure security keys
        configure_security_keys(secrets_manager)
        
        # Save all secrets
        print("\n💾 Saving secrets...")
        secrets_manager._save_secrets()
        
        # Validate configuration
        print("\n✅ Validating secrets configuration...")
        validation = secrets_manager.validate_secrets()
        
        if validation["valid"]:
            print("🎉 All required secrets are configured!")
        else:
            print("⚠️  Some required secrets are missing:")
            for missing in validation["missing_required"]:
                print(f"   - {missing}")
        
        print(f"\n📊 Configuration Summary:")
        print(f"   Total secrets: {validation['total_secrets']}")
        print(f"   Configured: {validation['configured_secrets']}")
        print(f"   Optional available: {len(validation['available_optional'])}")
        
        # Export environment file for development
        if input("\nExport .env file for development? [y/N]: ").lower().startswith('y'):
            secrets_manager.export_environment_file(".env.secrets")
            print("📄 Environment file exported to .env.secrets")
            print("   Remember to add .env.secrets to your .gitignore!")
        
        # Show next steps
        print("\n🎯 Next Steps:")
        print("1. Set PHOENIX_MASTER_KEY environment variable with your master key")
        print("2. Add .secrets/ directory to your .gitignore")
        print("3. Consider using keyring for additional security")
        print("4. Test your configuration with: python -c \"from scripts.setup_secrets import test_secrets; test_secrets()\"")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


def test_secrets():
    """Test secrets configuration"""
    print("🧪 Testing secrets configuration...")
    
    try:
        # Get master key from environment
        master_key = os.getenv("PHOENIX_MASTER_KEY")
        if not master_key:
            print("❌ PHOENIX_MASTER_KEY not found in environment")
            return False
        
        # Initialize secrets manager
        secrets_manager = SecretsManager(master_key=master_key)
        
        # Test n8n credentials
        n8n_creds = secrets_manager.get_n8n_credentials()
        print(f"✅ n8n user: {n8n_creds['user']}")
        print(f"✅ n8n password: {'*' * len(n8n_creds['password']) if n8n_creds['password'] else 'NOT SET'}")
        
        # Validate all secrets
        validation = secrets_manager.validate_secrets()
        if validation["valid"]:
            print("🎉 All secrets are valid!")
            return True
        else:
            print("⚠️  Some secrets are missing:")
            for missing in validation["missing_required"]:
                print(f"   - {missing}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    main()