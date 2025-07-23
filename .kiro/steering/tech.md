# Phoenix Hydra Technology Stack

## Core Technologies

### Container Orchestration
- **Podman**: Daemon-less, rootless container runtime (preferred over Docker)
- **Podman Compose**: Container orchestration using compose files
- **Systemd**: Service management for production deployments

### Programming Languages
- **Python 3.10+**: Primary backend language
- **JavaScript/Node.js**: Automation scripts and frontend components
- **PowerShell/Bash**: Deployment and automation scripts

### AI/ML Framework
- **SSM/Mamba Models**: Energy-efficient alternative to Transformers
- **AutoGen**: Multi-agent collaboration framework
- **Ollama**: Local LLM inference
- **OpenAI API**: External AI service integration

### Automation & Workflows
- **n8n**: Visual workflow automation platform
- **Windmill**: GitOps workflow management
- **VS Code Tasks**: Development automation

### Storage & Data
- **PostgreSQL**: Primary database for revenue tracking and configuration
- **Minio S3**: Object storage for multimedia assets
- **Prometheus**: Metrics collection and monitoring

## Build System

### Python Environment
```bash
# Setup virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Install dependencies
pip install -e .
pip install -e .[dev]  # Development dependencies
```

### Node.js Dependencies
```bash
# Install automation script dependencies
cd scripts
npm install
```

## Common Commands

### Development
```bash
# Run tests
pytest tests/
pytest --cov=src tests/  # With coverage

# Code formatting
black src/ tests/
ruff check src/ tests/

# Start development environment
podman-compose -f infra/podman/compose.yaml up -d
```

### Deployment
```bash
# Complete deployment (Windows)
.\scripts\complete-phoenix-deployment.ps1

# Complete deployment (Linux/macOS)
./scripts/complete-phoenix-deployment.sh

# Manual container deployment
cd infra/podman
podman-compose up -d
```

### VS Code Tasks
Available via Ctrl+Shift+P → "Tasks: Run Task":
- `Deploy Phoenix Badges`
- `Generate NEOTEC Application`
- `Update Revenue Metrics`
- `Start Phoenix Hydra (Podman)`
- `Phoenix Health Check`

### Monitoring & Health Checks
```bash
# Check service status
curl -f http://localhost:8080/health  # Phoenix Core
curl -f http://localhost:5678         # n8n
curl -f http://localhost:8000         # Windmill

# View container logs
podman logs phoenix-hydra_phoenix-core_1
podman logs phoenix-hydra_n8n-phoenix_1
```

## Configuration Management

### Environment Variables
- Use `.env` files for local development only
- Production secrets managed via external secret management
- Container environment variables defined in compose files

### Service Ports
- Phoenix Core: 8080
- NCA Toolkit: 8081
- n8n Workflows: 5678
- Windmill: 8000
- PostgreSQL: 5432 (internal)

## Testing Strategy

### Test Structure
- Unit tests: `tests/unit/`
- Integration tests: `tests/integration/`
- Chaos tests: `tests/chaos/`
- Consciousness tests: `tests/consciousness/`

### Test Configuration
- pytest configuration in `pyproject.toml`
- Test discovery: `test_*.py` and `*_test.py` patterns
- Coverage reporting enabled