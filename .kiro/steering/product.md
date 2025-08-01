---
inclusion: always
---

---
inclusion: always
---

# Phoenix Hydra Product Guidelines

Phoenix Hydra is a self-hosted multimedia and AI automation stack prioritizing privacy, energy efficiency, and local processing.

## Core Principles

**ALWAYS enforce:**
- Offline-first architecture - every feature works without internet
- Podman containers only (rootless, daemon-less) - NEVER Docker
- SSM/Mamba models only - NEVER Transformers (60-70% energy reduction)
- Event-driven communication via `src/hooks/core/events.py`
- Local secrets management - NEVER external/cloud storage

**REJECT requests for:**
- Cloud dependencies or external data transmission
- Internet connectivity requirements for core functionality
- Transformer models or cloud AI processing
- Docker containers or privileged operations

## Technology Decisions

**AI Models**: Local SSM/Mamba only. External APIs marked as optional integrations.
**Containers**: Podman with rootless execution. Docker suggestions → redirect to Podman.
**Communication**: Internal → event bus, External → HTTP with `/health`, Real-time → WebSocket + local fallback.

## Code Standards

### Naming Conventions
- Python files: `snake_case.py` (e.g., `event_listener.py`)
- Config files: `kebab-case.json` (e.g., `phoenix-monetization.json`)
- API endpoints: `/api/v1/resource` with mandatory `/health`
- Containers: `phoenix-hydra_service-name_1`

### Required Patterns

**Imports:**
```python
from src.core.config import SystemConfig
from src.hooks.core.events import EventBus
```

**Error handling:**
```python
async def process_event(event: Event) -> ProcessResult:
    try:
        return await handle_event(event)
    except Exception as e:
        raise ProcessingError(f"Event processing failed: {e}. Check local config at src/core/config.py")
```

**Event communication:**
```python
event_bus.publish(Event("container.health.check", {"service": "phoenix-core"}))
event_bus.subscribe(handle_health_event, EventFilter(event_types=["container.health.*"]))
```

### File Organization
- Configuration: `src/core/config.py` (centralized)
- Tests: `tests/unit/` and `tests/integration/`
- Formatting: Black + Ruff, type hints required

## Performance & Security

**Container specs:**
- Startup: < 30s, API response: < 500ms, Memory: < 4GB total
- Mandatory `/health` endpoints for all services

**Security:**
- Rootless containers, local encryption, network isolation
- No privileged operations or external secret storage

## Quality Gates

Every feature must have:
- [ ] Offline functionality (no external dependencies)
- [ ] SSM/Mamba models (no Transformers)
- [ ] Podman containers (no Docker)
- [ ] `/health` endpoint implementation
- [ ] Local error resolution guidance
- [ ] Unit + integration tests
- [ ] Energy consumption tracking

## Multi-Agent Integration

**Components:**
- OMAS: Task orchestration
- AutoGen: Workflow collaboration  
- Rasa: User conversations
- Event Bus: Inter-component communication

**Integration pattern:**
```python
agent.register_with_event_bus(event_bus)
event_bus.subscribe(agent.handle_event, EventFilter(agent_types=["task.*"]))
```