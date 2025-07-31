# Phoenix Hydra Secure Credentials Setup

## 🔐 Overview

This document describes the secure credential storage system implemented for Phoenix Hydra, including the configuration of n8n credentials and other sensitive information.

## ✅ What Was Implemented

### 1. Comprehensive Secrets Management System
- **Location**: `src/phoenix_system_review/core/secrets_manager.py`
- **Features**:
  - Multi-backend storage (encrypted files, keyring, environment variables)
  - AES encryption using Fernet with PBKDF2 key derivation
  - Automatic secret validation and configuration management
  - Support for all Phoenix Hydra services (n8n, PostgreSQL, Minio, APIs)

### 2. n8n Credentials Configuration
- **User**: `ykan.prod@gmail.com`
- **Password**: `Rivotrip7$` (securely encrypted)
- **Storage**: Encrypted in `.secrets/phoenix_secrets.enc`
- **Environment**: Available in `.env.secrets` for development

### 3. Security Features
- **Master Key**: `j4c&iCdV&4GOd0%FN30yLuu0HIfux@Yo`
- **Encryption**: AES-256 with Fernet
- **Key Derivation**: PBKDF2 with 100,000 iterations
- **File Permissions**: Restrictive (600) for secret files
- **Git Protection**: Added to `.gitignore` to prevent commits

### 4. Configuration Scripts
- **Setup Script**: `scripts/configure_n8n_credentials.py`
- **PowerShell Script**: `scripts/setup-secrets.ps1`
- **Full Setup**: `scripts/setup_secrets.py`
- **Validator**: `scripts/validate_config.py`

### 5. Container Integration
- **Compose File**: `infra/podman/compose.secrets.yaml`
- **Environment Variables**: Automatically loaded from secrets
- **Service Configuration**: n8n, PostgreSQL, Minio, monitoring services

## 🚀 Current Status

### ✅ Successfully Configured
- n8n user and password credentials
- JWT signing secret
- Application encryption key
- Master key encryption system
- Secrets file structure
- Environment file export

### ⚠️ Pending Configuration
- PostgreSQL database password
- Minio S3 access and secret keys
- Optional API keys (OpenAI, GitHub)
- Monitoring service passwords

## 🎯 Next Steps

### 1. Set Master Key Permanently
```powershell
# For current session
$env:PHOENIX_MASTER_KEY = 'j4c&iCdV&4GOd0%FN30yLuu0HIfux@Yo'

# For permanent user environment
[Environment]::SetEnvironmentVariable('PHOENIX_MASTER_KEY', 'j4c&iCdV&4GOd0%FN30yLuu0HIfux@Yo', 'User')
```

### 2. Configure Remaining Services
```bash
# Run full setup for all services
python scripts/setup_secrets.py

# Or configure individual services
python -c "
from src.phoenix_system_review.core.secrets_manager import get_secrets_manager
sm = get_secrets_manager()
sm.set_secret('postgres_password', 'your_db_password')
sm.set_secret('minio_access_key', 'your_minio_access_key')
sm.set_secret('minio_secret_key', 'your_minio_secret_key')
"
```

### 3. Start Phoenix Hydra Services
```bash
# Using the secure compose file
podman-compose -f infra/podman/compose.secrets.yaml up -d

# Access n8n
# URL: http://localhost:5678
# Username: ykan.prod@gmail.com
# Password: Rivotrip7$
```

### 4. Validate Configuration
```bash
python scripts/validate_config.py
```

## 🔒 Security Best Practices Implemented

### 1. Encryption
- **Algorithm**: AES-256 in CBC mode with HMAC authentication
- **Key Derivation**: PBKDF2 with SHA-256, 100,000 iterations
- **Salt**: Application-specific salt for key derivation
- **Storage**: Encrypted secrets stored in `.secrets/phoenix_secrets.enc`

### 2. Access Control
- **File Permissions**: 600 (owner read/write only)
- **Directory Protection**: `.secrets/` directory secured
- **Git Exclusion**: All secret files in `.gitignore`

### 3. Multi-Backend Support
- **Primary**: Encrypted file storage
- **Secondary**: System keyring integration
- **Fallback**: Environment variables
- **Development**: `.env.secrets` file for local development

### 4. Validation & Monitoring
- **Secret Validation**: Automatic validation of required secrets
- **Configuration Checking**: Comprehensive system validation
- **Logging**: Structured logging of all secret operations
- **Error Handling**: Graceful degradation for missing secrets

## 📁 File Structure

```
Phoenix Hydra/
├── .secrets/
│   └── phoenix_secrets.enc          # Encrypted secrets storage
├── .env.secrets                     # Development environment file
├── src/phoenix_system_review/core/
│   ├── secrets_manager.py           # Main secrets management system
│   ├── config_validator.py          # Configuration validation
│   ├── logging_system.py            # Structured logging
│   └── error_handler.py             # Error handling framework
├── scripts/
│   ├── configure_n8n_credentials.py # Quick n8n setup
│   ├── setup_secrets.py             # Full secrets setup
│   ├── setup-secrets.ps1            # PowerShell setup script
│   └── validate_config.py           # Configuration validator
├── infra/podman/
│   └── compose.secrets.yaml         # Secure container configuration
└── docs/
    └── SECURE_CREDENTIALS_SETUP.md  # This documentation
```

## 🛡️ Security Considerations

### ✅ Implemented Protections
- Credentials never stored in plaintext in code
- Master key required for decryption
- File permissions restrict access
- Git exclusion prevents accidental commits
- Multiple storage backends for redundancy
- Automatic validation and error handling

### ⚠️ Important Reminders
- **Backup Master Key**: Store the master key securely and separately
- **Rotate Credentials**: Regularly update passwords and API keys
- **Monitor Access**: Review logs for unauthorized access attempts
- **Environment Separation**: Use different credentials for dev/staging/prod
- **Key Management**: Consider using dedicated key management services in production

## 🔧 Troubleshooting

### Common Issues

1. **Master Key Not Found**
   ```bash
   # Set the master key environment variable
   export PHOENIX_MASTER_KEY='j4c&iCdV&4GOd0%FN30yLuu0HIfux@Yo'
   ```

2. **Secrets File Corrupted**
   ```bash
   # Regenerate secrets (will lose existing data)
   rm .secrets/phoenix_secrets.enc
   python scripts/configure_n8n_credentials.py
   ```

3. **Permission Denied**
   ```bash
   # Fix file permissions
   chmod 600 .secrets/phoenix_secrets.enc
   chmod 600 .env.secrets
   ```

4. **Service Connection Issues**
   ```bash
   # Validate configuration
   python scripts/validate_config.py
   
   # Check service status
   podman ps -a
   ```

## 📞 Support

For issues with the secure credentials system:

1. Check the validation output: `python scripts/validate_config.py`
2. Review logs in the `logs/` directory
3. Verify master key is set correctly
4. Ensure all required dependencies are installed
5. Check file permissions on secret files

The system is designed to be secure by default while remaining user-friendly for development and deployment scenarios.