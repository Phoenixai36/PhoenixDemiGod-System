"""
Secure secrets management system for Phoenix Hydra

This module provides secure storage and retrieval of sensitive credentials
including n8n authentication, database passwords, API keys, and other secrets.
"""

import os
import json
import base64
import hashlib
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import keyring
import logging

from .logging_system import get_logger


@dataclass
class SecretConfig:
    """Configuration for secret storage"""
    name: str
    description: str
    required: bool = True
    default_value: Optional[str] = None
    environment_var: Optional[str] = None
    keyring_service: Optional[str] = None
    encrypted: bool = True


class SecretsManager:
    """Secure secrets management with multiple storage backends"""
    
    def __init__(
        self,
        secrets_file: Optional[str] = None,
        master_key: Optional[str] = None,
        use_keyring: bool = True,
        use_environment: bool = True
    ):
        self.logger = get_logger()
        self.secrets_file = Path(secrets_file) if secrets_file else Path(".secrets/phoenix_secrets.enc")
        self.use_keyring = use_keyring
        self.use_environment = use_environment
        
        # Create secrets directory
        self.secrets_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize encryption
        self._cipher = None
        if master_key:
            self._setup_encryption(master_key)
        
        # Define secret configurations
        self.secret_configs = self._define_secret_configs()
        
        # Load existing secrets
        self._secrets_cache: Dict[str, str] = {}
        self._load_secrets()
    
    def _define_secret_configs(self) -> Dict[str, SecretConfig]:
        """Define all secret configurations for Phoenix Hydra"""
        return {
            # n8n Configuration
            "n8n_user": SecretConfig(
                name="n8n_user",
                description="n8n workflow automation user email",
                environment_var="N8N_USER",
                keyring_service="phoenix_hydra_n8n"
            ),
            "n8n_password": SecretConfig(
                name="n8n_password",
                description="n8n workflow automation password",
                environment_var="N8N_PASSWORD",
                keyring_service="phoenix_hydra_n8n"
            ),
            "n8n_api_key": SecretConfig(
                name="n8n_api_key",
                description="n8n API key for automation",
                environment_var="N8N_API_KEY",
                keyring_service="phoenix_hydra_n8n",
                required=False
            ),
            
            # Database Configuration
            "postgres_user": SecretConfig(
                name="postgres_user",
                description="PostgreSQL database username",
                environment_var="POSTGRES_USER",
                keyring_service="phoenix_hydra_db",
                default_value="phoenix_user"
            ),
            "postgres_password": SecretConfig(
                name="postgres_password",
                description="PostgreSQL database password",
                environment_var="POSTGRES_PASSWORD",
                keyring_service="phoenix_hydra_db"
            ),
            "postgres_db": SecretConfig(
                name="postgres_db",
                description="PostgreSQL database name",
                environment_var="POSTGRES_DB",
                keyring_service="phoenix_hydra_db",
                default_value="phoenix_hydra",
                encrypted=False
            ),
            
            # Minio S3 Configuration
            "minio_access_key": SecretConfig(
                name="minio_access_key",
                description="Minio S3 access key",
                environment_var="MINIO_ACCESS_KEY",
                keyring_service="phoenix_hydra_minio"
            ),
            "minio_secret_key": SecretConfig(
                name="minio_secret_key",
                description="Minio S3 secret key",
                environment_var="MINIO_SECRET_KEY",
                keyring_service="phoenix_hydra_minio"
            ),
            
            # API Keys
            "openai_api_key": SecretConfig(
                name="openai_api_key",
                description="OpenAI API key for AI services",
                environment_var="OPENAI_API_KEY",
                keyring_service="phoenix_hydra_apis",
                required=False
            ),
            "github_token": SecretConfig(
                name="github_token",
                description="GitHub personal access token",
                environment_var="GITHUB_TOKEN",
                keyring_service="phoenix_hydra_apis",
                required=False
            ),
            
            # Monitoring & Metrics
            "prometheus_password": SecretConfig(
                name="prometheus_password",
                description="Prometheus monitoring password",
                environment_var="PROMETHEUS_PASSWORD",
                keyring_service="phoenix_hydra_monitoring",
                required=False
            ),
            "grafana_admin_password": SecretConfig(
                name="grafana_admin_password",
                description="Grafana admin password",
                environment_var="GRAFANA_ADMIN_PASSWORD",
                keyring_service="phoenix_hydra_monitoring",
                required=False
            ),
            
            # Encryption Keys
            "jwt_secret": SecretConfig(
                name="jwt_secret",
                description="JWT signing secret",
                environment_var="JWT_SECRET",
                keyring_service="phoenix_hydra_crypto"
            ),
            "encryption_key": SecretConfig(
                name="encryption_key",
                description="Application encryption key",
                environment_var="ENCRYPTION_KEY",
                keyring_service="phoenix_hydra_crypto"
            )
        }
    
    def _setup_encryption(self, master_key: str):
        """Setup encryption cipher with master key"""
        try:
            # Derive key from master key
            salt = b'phoenix_hydra_salt_2024'  # In production, use random salt
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(master_key.encode()))
            self._cipher = Fernet(key)
            
            self.logger.info("Encryption initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to setup encryption: {e}")
            raise
    
    def _encrypt_value(self, value: str) -> str:
        """Encrypt a secret value"""
        if not self._cipher:
            return value  # Return plaintext if no encryption
        
        try:
            encrypted = self._cipher.encrypt(value.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            self.logger.error(f"Failed to encrypt value: {e}")
            return value
    
    def _decrypt_value(self, encrypted_value: str) -> str:
        """Decrypt a secret value"""
        if not self._cipher:
            return encrypted_value  # Return as-is if no encryption
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_value.encode())
            decrypted = self._cipher.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            self.logger.warning(f"Failed to decrypt value, returning as-is: {e}")
            return encrypted_value
    
    def _load_secrets(self):
        """Load secrets from file"""
        if not self.secrets_file.exists():
            self.logger.info("No secrets file found, starting with empty secrets")
            return
        
        try:
            with open(self.secrets_file, 'r') as f:
                encrypted_data = json.load(f)
            
            for key, encrypted_value in encrypted_data.items():
                if key in self.secret_configs and self.secret_configs[key].encrypted:
                    self._secrets_cache[key] = self._decrypt_value(encrypted_value)
                else:
                    self._secrets_cache[key] = encrypted_value
            
            self.logger.info(f"Loaded {len(self._secrets_cache)} secrets from file")
        except Exception as e:
            self.logger.error(f"Failed to load secrets file: {e}")
    
    def _save_secrets(self):
        """Save secrets to encrypted file"""
        try:
            encrypted_data = {}
            for key, value in self._secrets_cache.items():
                if key in self.secret_configs and self.secret_configs[key].encrypted:
                    encrypted_data[key] = self._encrypt_value(value)
                else:
                    encrypted_data[key] = value
            
            with open(self.secrets_file, 'w') as f:
                json.dump(encrypted_data, f, indent=2)
            
            # Set restrictive permissions
            os.chmod(self.secrets_file, 0o600)
            
            self.logger.info(f"Saved {len(encrypted_data)} secrets to file")
        except Exception as e:
            self.logger.error(f"Failed to save secrets file: {e}")
            raise
    
    def set_secret(self, name: str, value: str, save_to_file: bool = True):
        """Set a secret value with multiple storage options"""
        if name not in self.secret_configs:
            raise ValueError(f"Unknown secret: {name}")
        
        config = self.secret_configs[name]
        
        # Store in cache
        self._secrets_cache[name] = value
        
        # Store in keyring if available and configured
        if self.use_keyring and config.keyring_service:
            try:
                keyring.set_password(config.keyring_service, name, value)
                self.logger.debug(f"Stored {name} in keyring")
            except Exception as e:
                self.logger.warning(f"Failed to store {name} in keyring: {e}")
        
        # Save to encrypted file
        if save_to_file:
            self._save_secrets()
        
        self.logger.info(f"Secret {name} has been set")
    
    def get_secret(self, name: str) -> Optional[str]:
        """Get a secret value from multiple sources"""
        if name not in self.secret_configs:
            raise ValueError(f"Unknown secret: {name}")
        
        config = self.secret_configs[name]
        
        # Try environment variable first
        if self.use_environment and config.environment_var:
            env_value = os.getenv(config.environment_var)
            if env_value:
                self.logger.debug(f"Retrieved {name} from environment")
                return env_value
        
        # Try cache
        if name in self._secrets_cache:
            self.logger.debug(f"Retrieved {name} from cache")
            return self._secrets_cache[name]
        
        # Try keyring
        if self.use_keyring and config.keyring_service:
            try:
                keyring_value = keyring.get_password(config.keyring_service, name)
                if keyring_value:
                    self.logger.debug(f"Retrieved {name} from keyring")
                    return keyring_value
            except Exception as e:
                self.logger.warning(f"Failed to retrieve {name} from keyring: {e}")
        
        # Return default value if available
        if config.default_value:
            self.logger.debug(f"Using default value for {name}")
            return config.default_value
        
        # Return None if not found and not required
        if not config.required:
            return None
        
        # Raise error if required secret is missing
        raise ValueError(f"Required secret {name} not found in any storage backend")
    
    def delete_secret(self, name: str):
        """Delete a secret from all storage backends"""
        if name not in self.secret_configs:
            raise ValueError(f"Unknown secret: {name}")
        
        config = self.secret_configs[name]
        
        # Remove from cache
        self._secrets_cache.pop(name, None)
        
        # Remove from keyring
        if self.use_keyring and config.keyring_service:
            try:
                keyring.delete_password(config.keyring_service, name)
                self.logger.debug(f"Deleted {name} from keyring")
            except Exception as e:
                self.logger.warning(f"Failed to delete {name} from keyring: {e}")
        
        # Save updated cache to file
        self._save_secrets()
        
        self.logger.info(f"Secret {name} has been deleted")
    
    def list_secrets(self, include_values: bool = False) -> Dict[str, Any]:
        """List all configured secrets and their status"""
        secrets_status = {}
        
        for name, config in self.secret_configs.items():
            status = {
                "description": config.description,
                "required": config.required,
                "has_value": self.get_secret(name) is not None,
                "sources": []
            }
            
            # Check which sources have the secret
            if self.use_environment and config.environment_var and os.getenv(config.environment_var):
                status["sources"].append("environment")
            
            if name in self._secrets_cache:
                status["sources"].append("file")
            
            if self.use_keyring and config.keyring_service:
                try:
                    if keyring.get_password(config.keyring_service, name):
                        status["sources"].append("keyring")
                except Exception:
                    pass
            
            if include_values and status["has_value"]:
                try:
                    value = self.get_secret(name)
                    # Mask sensitive values
                    if value and len(value) > 4:
                        status["value"] = value[:2] + "*" * (len(value) - 4) + value[-2:]
                    else:
                        status["value"] = "***"
                except Exception:
                    status["value"] = "ERROR"
            
            secrets_status[name] = status
        
        return secrets_status
    
    def validate_secrets(self) -> Dict[str, Any]:
        """Validate that all required secrets are available"""
        validation_results = {
            "valid": True,
            "missing_required": [],
            "available_optional": [],
            "total_secrets": len(self.secret_configs),
            "configured_secrets": 0
        }
        
        for name, config in self.secret_configs.items():
            try:
                value = self.get_secret(name)
                if value:
                    validation_results["configured_secrets"] += 1
                    if not config.required:
                        validation_results["available_optional"].append(name)
                else:
                    if config.required:
                        validation_results["missing_required"].append(name)
                        validation_results["valid"] = False
            except Exception as e:
                if config.required:
                    validation_results["missing_required"].append(name)
                    validation_results["valid"] = False
                self.logger.error(f"Error validating secret {name}: {e}")
        
        return validation_results
    
    def get_n8n_credentials(self) -> Dict[str, str]:
        """Get n8n credentials as a dictionary"""
        return {
            "user": self.get_secret("n8n_user"),
            "password": self.get_secret("n8n_password"),
            "api_key": self.get_secret("n8n_api_key")
        }
    
    def get_database_credentials(self) -> Dict[str, str]:
        """Get database credentials as a dictionary"""
        return {
            "user": self.get_secret("postgres_user"),
            "password": self.get_secret("postgres_password"),
            "database": self.get_secret("postgres_db")
        }
    
    def get_minio_credentials(self) -> Dict[str, str]:
        """Get Minio S3 credentials as a dictionary"""
        return {
            "access_key": self.get_secret("minio_access_key"),
            "secret_key": self.get_secret("minio_secret_key")
        }
    
    def export_environment_file(self, file_path: str = ".env.secrets"):
        """Export secrets as environment file for development"""
        env_lines = []
        env_lines.append("# Phoenix Hydra Secrets - Generated automatically")
        env_lines.append("# DO NOT COMMIT THIS FILE TO VERSION CONTROL")
        env_lines.append("")
        
        for name, config in self.secret_configs.items():
            if config.environment_var:
                try:
                    value = self.get_secret(name)
                    if value:
                        env_lines.append(f"{config.environment_var}={value}")
                    else:
                        env_lines.append(f"# {config.environment_var}=  # {config.description}")
                except Exception:
                    env_lines.append(f"# {config.environment_var}=  # {config.description} (ERROR)")
        
        with open(file_path, 'w') as f:
            f.write('\n'.join(env_lines))
        
        # Set restrictive permissions
        os.chmod(file_path, 0o600)
        
        self.logger.info(f"Exported environment file to {file_path}")
    
    def import_from_environment_file(self, file_path: str = ".env"):
        """Import secrets from environment file"""
        if not Path(file_path).exists():
            self.logger.warning(f"Environment file {file_path} not found")
            return
        
        imported_count = 0
        
        with open(file_path, 'r') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Find secret by environment variable
                for name, config in self.secret_configs.items():
                    if config.environment_var == key and value:
                        self.set_secret(name, value, save_to_file=False)
                        imported_count += 1
                        break
        
        if imported_count > 0:
            self._save_secrets()
            self.logger.info(f"Imported {imported_count} secrets from {file_path}")
        else:
            self.logger.info(f"No secrets imported from {file_path}")


# Global secrets manager instance
_global_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager(master_key: Optional[str] = None) -> SecretsManager:
    """Get the global secrets manager instance"""
    global _global_secrets_manager
    if _global_secrets_manager is None:
        _global_secrets_manager = SecretsManager(master_key=master_key)
    return _global_secrets_manager


def setup_secrets_manager(
    secrets_file: Optional[str] = None,
    master_key: Optional[str] = None,
    **kwargs
) -> SecretsManager:
    """Setup global secrets manager"""
    global _global_secrets_manager
    _global_secrets_manager = SecretsManager(
        secrets_file=secrets_file,
        master_key=master_key,
        **kwargs
    )
    return _global_secrets_manager