# Phoenix Hydra Project Structure

## Root Directory Organization

### Core Application Code
- `src/` - Main source code directory
  - `agents/` - Multi-agent system implementations (OMAS, AutoGen, Rasa)
  - `core/` - Core system components and routing logic
  - `containers/` - Container management and event handling
  - `dashboard/` - Web dashboard and UI components
  - `hooks/` - Event-driven automation system with file watchers
  - `integration/` - External service integrations
  - `metrics/` - Performance monitoring and data collection
  - `phoenix_demigod/` - Main Phoenix DemiGod v8.7 system
  - `phoenixxhydra/` - Phoenix Hydra specific implementations
  - `scheduler/` - Task scheduling and workflow management
  - `services/` - Microservice implementations
  - `utils/` - Shared utilities and helper functions

### Infrastructure & Deployment
- `infra/` - Infrastructure as code and deployment configurations
  - `podman/` - Podman compose files and container configurations
- `scripts/` - Automation and deployment scripts
  - Node.js automation scripts with package.json
  - PowerShell deployment scripts for Windows
  - Python utilities for grant applications and revenue tracking

### Configuration & Documentation
- `configs/` - Application configuration files
  - `n8n-workflows/` - n8n workflow definitions
  - `phoenix-monetization.json` - Monetization configuration
- `docs/` - Project documentation and guides
- `windmill-scripts/` - Windmill workflow configurations

### Testing & Quality Assurance
- `tests/` - Comprehensive test suite
  - `unit/` - Unit tests for individual components
  - `integration/` - Integration tests for system interactions
  - `chaos/` - Chaos engineering tests
  - `consciousness/` - AI consciousness and behavior tests
  - `metrics/` - Performance and metrics testing

### Development Environment
- `.vscode/` - VS Code configuration with automated tasks
- `.kiro/` - Kiro IDE steering rules and configuration
- `venv/`, `.venv/`, `venv2/`, `venv3/` - Python virtual environments

## Key Architectural Patterns

### Modular Agent System
- Each agent type has its own directory under `src/agents/`
- Agents communicate through event bus system in `src/hooks/`
- Configuration managed centrally in `src/core/config.py`

### Container-First Architecture
- All services containerized using Podman
- Rootless, daemon-less container execution
- Systemd integration for production deployments
- Health checks and monitoring built-in

### Event-Driven Automation
- File system watchers in `src/hooks/event_sources/`
- Container event listeners in `src/containers/event_listener.py`
- Centralized event bus for component communication

### Multi-Environment Support
- Development: Local Podman compose
- Staging: Kubernetes-ready configurations
- Production: Systemd service management

## File Naming Conventions

### Python Files
- Snake_case for modules: `event_listener.py`
- Test files prefixed: `test_*.py`
- Configuration files: `config.py`, `settings.py`

### Configuration Files
- JSON for structured data: `phoenix-monetization.json`
- YAML for compose files: `compose.yaml`
- Environment files: `.env` (development only)

### Scripts
- PowerShell: `.ps1` extension
- Bash: `.sh` extension
- Node.js: `.js` extension with package.json

## Import Patterns

### Relative Imports
```python
from src.core.config import SystemConfig
from src.hooks.core.events import EventBus
from src.containers.event_listener import ContainerEventListener
```

### Package Structure
- Each major component is a Python package with `__init__.py`
- Shared utilities accessible via `src.utils`
- Configuration centralized in `src.core.config`

## Development Workflow

### Local Development
1. Activate Python virtual environment
2. Install dependencies with `pip install -e .[dev]`
3. Start services with VS Code task or `podman-compose up -d`
4. Run tests with `pytest tests/`

### Code Organization Principles
- Single responsibility per module
- Clear separation between core logic and infrastructure
- Configuration externalized from code
- Comprehensive test coverage for all components
- Event-driven architecture for loose coupling

## Special Directories

### Generated Content
- `build/` - Build artifacts (gitignored)
- `build_output/` - Deployment packages
- `logs/` - Application logs
- `monitoring/` - Grafana dashboards and configs

### External Dependencies
- `node_modules/` - Node.js dependencies (gitignored)
- `models/` - AI model storage
- `training/` - ML training data and scripts

### Legacy/Archive
- `awesome-n8n-templates-main/` - External template repository
- `claude-code-ui/` - Legacy UI components
- Various versioned virtual environments