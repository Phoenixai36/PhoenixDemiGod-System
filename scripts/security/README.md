# Phoenix Hydra Security Management

Comprehensive dependency security management system for Phoenix Hydra, providing automated vulnerability detection, dependency validation, and update management while maintaining the system's offline-first and privacy-focused architecture.

## Overview

This security management system addresses the systematic management of npm dependencies and security vulnerabilities in the Phoenix Hydra dashboard project. It provides:

- **Automated Security Scanning**: Detects vulnerabilities using npm audit and OSV database
- **Phoenix Hydra Validation**: Ensures dependencies comply with offline-first and privacy requirements
- **Automated Updates**: Manages security patches with testing and rollback capabilities
- **Audit Logging**: Comprehensive audit trail for all security actions
- **Emergency Response**: Fast-track procedures for critical vulnerabilities

## Architecture

```
scripts/security/
├── base/                    # Base classes and interfaces
│   ├── interfaces.py       # Abstract base classes
│   ├── config.py          # Configuration management
│   ├── exceptions.py      # Custom exceptions
│   └── utils.py           # Utility functions
├── config/                 # Configuration files
│   ├── security-config.json
│   └── phoenix-hydra-validation-rules.json
├── scanners/              # Security scanner implementations
├── validators/            # Dependency validators
├── updaters/              # Update management
├── security_manager.py    # Main security manager
├── cli.py                 # Command-line interface
└── README.md              # This file

.phoenix-hydra/security/   # Local security data
├── vulnerability-db.sqlite
├── audit-logs/
└── reports/
```

## Quick Start

### 1. Initialize Security Infrastructure

```bash
# Initialize the security system
python scripts/security/cli.py init

# Check system status
python scripts/security/cli.py status

# Perform health check
python scripts/security/cli.py health
```

### 2. Configuration

The security system uses configuration files in `scripts/security/config/`:

- `security-config.json`: Main security configuration
- `phoenix-hydra-validation-rules.json`: Phoenix Hydra specific validation rules

View current configuration:
```bash
python scripts/security/cli.py config

# Validate configuration
python scripts/security/cli.py config --validate
```

### 3. Using the Security Manager

```python
from scripts.security.security_manager import create_security_manager

# Create and initialize security manager
manager = await create_security_manager()

# Scan for vulnerabilities
vulnerabilities = await manager.scan_dependencies()

# Validate a dependency
result = await manager.validate_dependency("react-syntax-highlighter", "15.6.1")

# Process security updates
updates = await manager.process_security_updates()

# Generate security report
report = await manager.generate_security_report()
```

## Phoenix Hydra Validation Rules

The system enforces Phoenix Hydra specific requirements:

### Offline Compatibility
- No external CDN dependencies
- No remote API calls without offline fallback
- No network-required dependencies

### Privacy Compliance
- No telemetry collection
- No user tracking
- Privacy-compatible licenses

### Container Compatibility
- No root privileges required
- No privileged ports
- No system directory writes

### Security Requirements
- No known critical vulnerabilities
- No known high vulnerabilities
- Secure dependency chain

## Configuration Options

### Vulnerability Thresholds
```json
{
  "vulnerability_thresholds": {
    "critical_block_build": true,
    "high_block_build": true,
    "moderate_block_build": false,
    "low_block_build": false,
    "phoenix_core_escalation": true
  }
}
```

### Scanner Configuration
```json
{
  "scanner": {
    "npm_audit_enabled": true,
    "osv_database_enabled": true,
    "offline_mode": false,
    "scan_interval_minutes": 30
  }
}
```

### Update Management
```json
{
  "update_manager": {
    "auto_apply_security_patches": true,
    "auto_apply_patch_updates": false,
    "require_tests_pass": true,
    "emergency_rollback_enabled": true
  }
}
```

## Directory Structure

### Local Security Database
```
.phoenix-hydra/security/
├── vulnerability-db.sqlite    # Local vulnerability database
├── last-update.json          # Database update timestamp
├── security-metrics.json     # Security metrics and trends
├── audit-logs/               # Security audit trail
│   ├── 2024-01-15.log
│   └── 2024-01-16.log
└── reports/                  # Generated security reports
    ├── daily/
    ├── weekly/
    └── compliance/
```

## Implementation Status

### ✅ Completed (Task 1)
- [x] Security management directory structure
- [x] Local vulnerability database storage
- [x] Configuration files and validation rules
- [x] Base classes and interfaces
- [x] Security manager coordination
- [x] CLI interface for testing

### 🚧 In Progress
- [ ] Security scanner implementation (Task 2)
- [ ] Dependency validator implementation (Task 3)
- [ ] Update manager implementation (Task 4)
- [ ] Audit logging implementation (Task 5)
- [ ] Workflow integration (Task 6)

## Error Handling

The system includes comprehensive error handling with specific exception types:

- `SecurityError`: Base security exception
- `VulnerabilityDetectionError`: Vulnerability scanning failures
- `DependencyValidationError`: Dependency validation failures
- `PhoenixHydraComplianceError`: Phoenix Hydra compliance violations
- `UpdateError`: Dependency update failures
- `ConfigurationError`: Configuration issues

## Logging and Monitoring

Security actions are logged with structured metadata:

```python
{
  "timestamp": "2024-01-15T10:30:00Z",
  "action": "vulnerability_scan",
  "package": "react-syntax-highlighter",
  "severity": "high",
  "phoenix_hydra_impact": "blocking",
  "resolution": "update_applied"
}
```

## Development

### Running Tests
```bash
# Run security component tests (when implemented)
pytest tests/security/ -v

# Run with coverage
pytest tests/security/ --cov=scripts.security
```

### Adding New Validators
1. Implement the `DependencyValidator` interface
2. Add validation rules to `phoenix-hydra-validation-rules.json`
3. Register the validator in the security manager
4. Add tests for the new validator

### Adding New Scanners
1. Implement the `SecurityScanner` interface
2. Add scanner configuration options
3. Register the scanner in the security manager
4. Add tests for the new scanner

## Troubleshooting

### Common Issues

**Configuration Validation Errors**
```bash
python scripts/security/cli.py config --validate
```

**Directory Permission Issues**
```bash
# Ensure directories are writable
chmod -R 755 .phoenix-hydra/security/
```

**Database Connection Issues**
```bash
# Check database path in configuration
python scripts/security/cli.py config
```

### Debug Mode
Enable debug mode in `security-config.json`:
```json
{
  "debug_mode": true
}
```

## Contributing

1. Follow Phoenix Hydra coding standards
2. Add tests for new functionality
3. Update documentation
4. Ensure offline compatibility
5. Validate privacy compliance

## License

Part of the Phoenix Hydra project. See main project license for details.