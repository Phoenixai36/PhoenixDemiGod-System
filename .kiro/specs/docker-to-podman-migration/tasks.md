# Implementation Plan

- [x] 1. Create Podman infrastructure directory structure
  - Create `infra/podman/` directory with subdirectories for each service
  - Set up proper directory structure: `gap-detector/`, `recurrent-processor/`, `rubik-agent/`, `nginx/`, `analysis-engine/`
  - Create configuration directories for each service
  - _Requirements: 1.3, 3.1_

- [x] 2. Convert main Dockerfile to Containerfile for recurrent-processor
  - Create `infra/podman/recurrent-processor/Containerfile` with rootless user configuration
  - Add non-root user creation and proper file permissions
  - Update Python dependency installation to use `--user` flag
  - Implement multi-stage build for optimization
  - _Requirements: 2.1, 2.2, 6.1_

- [x] 3. Convert gap-detector Dockerfile to Containerfile
  - Create `infra/podman/gap-detector/Containerfile` with security optimizations
  - Add proper user namespace mapping and non-root execution
  - Create separate requirements file for gap-detector dependencies
  - Implement proper file ownership and permissions
  - _Requirements: 2.1, 2.3, 6.2_

- [x] 4. Convert rubik-agent Dockerfile to Containerfile
  - Fix the malformed Dockerfile (currently has "kFROM" typo)
  - Create proper `infra/podman/rubik-agent/Containerfile` with Alpine base
  - Add meaningful application logic or placeholder service
  - Implement rootless execution with proper user configuration
  - _Requirements: 2.1, 2.4_

- [x] 5. Convert nginx Dockerfile to Containerfile
  - Create `infra/podman/nginx/Containerfile` with nginx configuration
  - Set up proper volume mounting for configuration files
  - Configure nginx to run as non-root user
  - Update nginx.conf for rootless execution compatibility
  - _Requirements: 2.1, 2.3, 5.3_

- [x] 6. Convert analysis-engine Dockerfile to Containerfile
  - Create `infra/podman/analysis-engine/Containerfile` (currently commented in compose)
  - Implement proper dependency management with requirements.txt
  - Add rootless user configuration and security optimizations
  - Set up proper working directory and file permissions
  - _Requirements: 2.1, 2.2_

- [x] 7. Create Podman-compatible compose configuration
  - Create `infra/podman/podman-compose.yaml` with all service definitions
  - Update service configurations for Podman networking
  - Add proper volume definitions with rootless-compatible paths
  - Configure security options and user namespace mapping
  - _Requirements: 3.1, 3.2, 5.1_

- [x] 8. Implement Podman networking configuration
  - Define `phoenix-net` network with proper subnet and gateway configuration
  - Set up DNS resolution between services
  - Configure exposed ports (8000, 3000, 8080, 5000)
  - Implement network isolation and security boundaries
  - _Requirements: 5.1, 5.2, 5.4_

- [x] 9. Configure Podman volume management
  - Set up `db_data` volume with proper rootless permissions
  - Create nginx configuration volume with correct ownership
  - Implement proper user namespace mapping for volumes
  - Add volume cleanup and management scripts
  - _Requirements: 3.3, 5.3, 6.2_

- [x] 10. Update deployment script for Podman
  - Replace docker-compose with podman-compose
  - Add Podman installation verification and setup functions
  - Implement rootless environment preparation (directories, permissions)
  - Add enhanced error handling and user guidance
  - _Requirements: 4.1, 4.4, 6.1_

- [x] 11. Update teardown script for Podman
  - Modify `teardown.sh` to detect and use both podman-compose and docker-compose
  - Add proper cleanup commands for containers, networks, and volumes
  - Implement error handling for rootless cleanup
  - _Requirements: 4.3, 4.4_

- [x] 12. Update verification script for Podman
  - Modify `verify.sh` to work with both podman-compose and docker-compose
  - Update service health verification logic for Podman containers
  - Add service status checking for all defined services
  - _Requirements: 4.2, 4.4_

- [x] 13. Create requirements.txt files for each service
  - Create `requirements-gap-detector.txt` with numpy and torch dependencies
  - Create `requirements-recurrent.txt` with torch and numpy dependencies
  - Create `requirements-analysis-engine.txt` with comprehensive dependencies
  - Create `requirements-rubik-agent.txt` with service-specific dependencies
  - _Requirements: 2.2, 2.4_

- [x] 14. Implement Podman build and deployment functionality
  - Integrate building functionality into comprehensive `deploy.sh` script
  - Add individual service build capabilities with proper error handling
  - Implement build optimization with layer caching
  - Add image tagging and versioning logic
  - _Requirements: 2.2, 4.1_

- [x] 15. Create Podman environment setup functionality
  - Integrate environment setup into `deploy.sh` script
  - Add Podman installation verification and configuration
  - Implement rootless setup with proper user namespace configuration
  - Add directory creation and permission setup
  - _Requirements: 6.1, 6.2, 4.1_

- [x] 16. Implement service health checks for Podman
  - Add health check verification to deployment script
  - Create health check logic for each service (gap-detector, windmill, nginx, analysis-engine)
  - Implement proper health check configuration in podman-compose.yaml
  - Add monitoring and status reporting for service health
  - _Requirements: 4.2, 5.2_

- [x] 17. Create comprehensive migration validation tests
  - Write integration tests to verify all services start correctly with Podman
  - Create network connectivity tests between services
  - Implement data persistence tests for PostgreSQL volume
  - Add performance comparison tests between Docker and Podman setups
  - _Requirements: 1.3, 3.2, 5.2_

- [x] 18. Update VS Code tasks for Podman
  - Modify `.vscode/tasks.json` to use podman-compose commands
  - Add Podman-specific tasks for building, starting, and stopping services
  - Create debugging tasks for individual service troubleshooting
  - Implement log viewing tasks for Podman containers
  - _Requirements: 4.1, 4.4_

- [x] 19. Create comprehensive Podman documentation
  - Write comprehensive migration guide from Docker to Podman
  - Create troubleshooting documentation for common Podman issues
  - Add performance tuning guide for Podman containers
  - Document security best practices for rootless execution
  - Consolidate existing README files and documentation
  - _Requirements: 4.4, 6.4_

- [x] 20. Implement rollback mechanism
  - Create rollback scripts to revert to Docker if needed
  - Add backup procedures for current Docker configuration
  - Implement validation checks before migration
  - Create recovery procedures for failed migration scenarios
  - _Requirements: 1.4, 4.4_

- [x] 21. Add model-service integration to compose configuration
  - Update `infra/podman/podman-compose.yaml` to include model-service with proper configuration
  - Configure model-service with appropriate volumes for model cache and config
  - Set up proper networking and health checks for model-service
  - Ensure model-service integrates with existing Phoenix Hydra services
  - _Requirements: 2.1, 3.1, 5.1_

- [x] 22. Create systemd integration for production deployment
  - Create systemd service files for Phoenix Hydra pod and individual services
  - Implement Quadlet configuration files for container management
  - Set up automatic startup and dependency management
  - Add systemd-based health monitoring and restart policies
  - _Requirements: 4.1, 4.2, 6.1_

- [x] 23. Implement comprehensive monitoring and observability
  - Add Prometheus metrics collection for all services
  - Create Grafana dashboards for Phoenix Hydra monitoring
  - Implement centralized logging with structured log format
  - Set up alerting for service failures and performance issues
  - _Requirements: 4.2, 5.2_

- [x] 24. Enhance security configuration and compliance
  - Implement custom seccomp profiles for enhanced container security
  - Add AppArmor/SELinux profiles for additional security layers
  - Create security scanning automation for container images
  - Implement secrets rotation and management procedures
  - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 25. Create automated testing and CI/CD integration
  - Implement automated testing pipeline for Podman deployment
  - Create GitHub Actions workflow for container building and testing
  - Add automated security scanning in CI/CD pipeline
  - Implement deployment validation and rollback automation
  - _Requirements: 1.3, 4.4_