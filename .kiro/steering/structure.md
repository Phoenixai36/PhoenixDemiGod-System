---
inclusion: always
---

---
inclusion: always
---

# Phoenix Hydra Project Structure

Phoenix Hydra uses event-driven architecture with modular components. All communication flows through the central event bus.

## File Placement Rules

### Source Code (`src/`)
- **Agent implementations** → `src/agents/{agent_type}/`
- **Core system components** → `src/core/`
- **Event handling & hooks** → `src/hooks/`
- **Container management** → `src/containers/`
- **Microservices** → `src/services/`
- **Shared utilities** → `src/utils/`

### Configuration & Infrastructure
- **App configuration** → `configs/` (JSON files)
- **Container configs** → `infra/podman/` (YAML files)
- **Automation scripts** → `scripts/` (PS1, Python, JS)
- **Workflow definitions** → `windmill-scripts/` (JSON)

### Testing
- **Unit tests** → `tests/unit/` (mirror src structure)
- **Integration tests** → `tests/integration/`
- **Test fixtures** → `tests/fixtures/`

## Naming Conventions

**ALWAYS use these patterns:**
- Python modules: `snake_case.py` (e.g., `event_listener.py`)
- Test files: `test_{module_name}.py`
- Config files: `kebab-case.json` (e.g., `phoenix-monetization.json`)
- Container services: `phoenix-hydra_{service-name}_1`
- Scripts: Descriptive names with proper extensions (`.ps1`, `.py`, `.js`)

## Required Import Patterns

**Standard imports for Phoenix Hydra:**
```python
# Core system
from src.core.config import SystemConfig
from src.core.router import Router

# Event system (ALWAYS use for communication)
from src.hooks.core.events import EventBus, Event, EventFilter

# Container management
from src.containers.event_listener import ContainerEventListener

# Utilities
from src.utils import logger, metrics
```

## Event-Driven Architecture Rules

**DO:**
- Use event bus for all inter-component communication
- Subscribe to events with proper filters
- Publish events for state changes
- Handle events asynchronously

**DON'T:**
- Direct imports between agents
- Synchronous blocking calls between services
- Hardcoded service dependencies

**Event pattern:**
```python
# Publishing events
event_bus.publish(Event("container.health.check", {"service": "phoenix-core"}))

# Subscribing to events
event_bus.subscribe(handle_event, EventFilter(event_types=["container.*"]))
```

## Code Organization Rules

### Module Structure
- Each `src/` subdirectory is a Python package with `__init__.py`
- One class per file (except small helper classes)
- Configuration centralized in `src/core/config.py`
- All logging through `src/utils/logger.py`

### New Component Checklist
When adding new components:
1. Create in appropriate `src/` subdirectory
2. Add `__init__.py` if creating new package
3. Register with event bus if needed
4. Add corresponding tests in `tests/`
5. Update configuration in `src/core/config.py`
6. Add health check endpoint if it's a service

### File Dependencies
- Core components can import from `utils/`
- Agents can only import from `core/` and `utils/`
- Services communicate only via event bus
- Tests can import from any `src/` module