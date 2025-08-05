# Phoenix Hydra Documentation

This directory contains comprehensive documentation for the Phoenix Hydra system, with a focus on Podman-based container deployment and management.

## Documentation Structure

### Core Documentation
- **[Podman Comprehensive Guide](podman-comprehensive-guide.md)** - Complete guide covering migration, deployment, and management
- **[Podman Troubleshooting](podman-troubleshooting.md)** - Detailed troubleshooting for common issues
- **[Podman Performance Tuning](podman-performance-tuning.md)** - Performance optimization strategies
- **[Podman Security Best Practices](podman-security-best-practices.md)** - Security hardening and compliance

### Legacy Documentation (Consolidated)
- **[Podman Migration Guide](podman-migration-guide.md)** - Original migration documentation
- **[Podman Deployment Guide](podman/podman_deployment_guide.md)** - Spanish deployment guide

### Service-Specific Documentation
- **[Gap Detector Service](../infra/podman/gap-detector/README.md)** - Gap detection and analysis service
- **[Analysis Engine](../infra/podman/analysis-engine/README.md)** - SSM-based analysis engine
- **[Nginx Proxy](../infra/podman/nginx/README.md)** - Reverse proxy configuration
- **[RUBIK Agent](../infra/podman/rubik-agent/README.md)** - Biomimetic agent service
- **[Podman Infrastructure](../infra/podman/README.md)** - Main infrastructure documentation

### Additional Resources
- **[Testing Guide](testing_guide.md)** - Testing strategies and procedures
- **[Migration Testing](migration-testing.md)** - Migration validation procedures
- **[Deployment Guide](deployment-guide.md)** - General deployment information
- **[CI/CD Guide](ci-cd.md)** - Continuous integration and deployment

## Quick Start

For new users, start with the **[Podman Comprehensive Guide](podman-comprehensive-guide.md)** which provides:

1. **Migration from Docker** - Step-by-step migration process
2. **Installation and Setup** - System requirements and installation
3. **Deployment Methods** - Multiple deployment approaches
4. **Troubleshooting** - Common issues and solutions
5. **Performance Tuning** - Optimization strategies
6. **Security Best Practices** - Security hardening

## Documentation Hierarchy

```
docs/
├── README.md (this file)
├── podman-comprehensive-guide.md      # 🎯 START HERE
├── podman-troubleshooting.md          # Problem solving
├── podman-performance-tuning.md       # Optimization
├── podman-security-best-practices.md  # Security
├── podman-migration-guide.md          # Legacy migration guide
└── podman/
    └── podman_deployment_guide.md     # Spanish deployment guide
```

## Service Documentation

Each Phoenix Hydra service has dedicated documentation:

### Core Services
- **Gap Detector** - Analyzes system gaps and migration status
- **Analysis Engine** - SSM-based AI analysis with energy efficiency
- **Nginx** - Reverse proxy and load balancer
- **RUBIK Agent** - Biomimetic agent system gateway

### Infrastructure Services
- **PostgreSQL** - Database for data persistence
- **Windmill** - Workflow management system

## Key Features Covered

### Security
- Rootless container execution
- User namespace mapping
- Network isolation
- Secrets management
- Compliance and auditing

### Performance
- Resource optimization
- Storage performance
- Network tuning
- Build optimization
- Monitoring and profiling

### Operations
- Health monitoring
- Backup procedures
- Update processes
- Incident response
- Maintenance tasks

## Getting Help

### Documentation Issues
If you find issues with the documentation:
1. Check the troubleshooting guide first
2. Review service-specific README files
3. Consult the comprehensive guide for detailed information

### Support Resources
- **Troubleshooting Guide**: Detailed problem-solving procedures
- **Performance Guide**: Optimization strategies and monitoring
- **Security Guide**: Best practices and compliance requirements
- **Service READMEs**: Service-specific configuration and usage

### Community Resources
- **Podman Documentation**: https://docs.podman.io/
- **Container Best Practices**: https://developers.redhat.com/blog/2019/04/25/podman-basics-cheat-sheet
- **Phoenix Hydra Issues**: Project issue tracker for bug reports and feature requests

## Documentation Maintenance

This documentation is actively maintained and updated with:
- New features and capabilities
- Troubleshooting solutions
- Performance optimizations
- Security updates
- Community feedback

### Contributing
When updating documentation:
1. Follow the established structure and format
2. Include practical examples and code snippets
3. Update cross-references when adding new content
4. Test all commands and procedures
5. Keep security and performance considerations in mind

### Version Information
- **Last Updated**: February 2025
- **Phoenix Hydra Version**: 1.0.0
- **Podman Version**: 4.0+
- **Documentation Version**: 2.0

This documentation provides comprehensive coverage of Phoenix Hydra's Podman-based infrastructure, from basic deployment to advanced security and performance optimization.