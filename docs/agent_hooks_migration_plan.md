# Plan de Migración de Agent Hooks

Este documento detalla el plan para migrar los "Agent Hooks" heredados a la nueva arquitectura basada en eventos en el proyecto Phoenix Hydra.

## 1. Estado Actual

### 1.1. Resumen

La refactorización de los Agent Hooks es una iniciativa crucial para mejorar la modularidad, la capacidad de prueba y la mantenibilidad del sistema.  La infraestructura central para la nueva arquitectura está completada, pero la migración de los hooks individuales está en sus primeras etapas.

### 1.2. Hooks Pendientes de Migración

Los siguientes hooks necesitan ser migrados a la nueva arquitectura:

*   Cellular Communication Hook
*   Container Health Restart Hook
*   Container Log Analysis Hook
*   Container Resource Scaling Hook

### 1.3. Ubicación del Código Antiguo

*   **Cellular Communication Hook:** Implementado dentro del sistema `phoenixxhydra`, específicamente en el directorio [`src/phoenixxhydra/networking/ccp/`](src/phoenixxhydra/networking/ccp/).
*   **Hooks de Contenedores (Container Health Restart, Container Log Analysis, Container Resource Scaling):** Implementados en la clase `KiroAgentHooks` en [`src/phoenix_system_review/automation/kiro_hooks.py`](src/phoenix_system_review/automation/kiro_hooks.py).

### 1.4. Nueva Arquitectura

La nueva arquitectura se basa en un bus de eventos asíncrono (`EventBus` en [`src/hooks/core/events.py`](src/hooks/core/events.py)) y clases de configuración centralizadas (en [`src/hooks/core/config.py`](src/hooks/core/config.py)).

## 2. Guía de Migración: Container Health Restart Hook

Esta sección proporciona una guía paso a paso para migrar el "Container Health Restart Hook" como ejemplo. Esta guía puede ser adaptada para migrar los hooks restantes.

### 2.1. Paso 1: Definir el Evento

Primero, defina un nuevo tipo de evento para representar un cambio en el estado de salud de un contenedor.  Cree un nuevo fichero [`src/hooks/events/container_health.py`](src/hooks/events/container_health.py) con el siguiente contenido:

```python
from dataclasses import dataclass
from src.hooks.core.events import Event

@dataclass
class ContainerHealthChangedEvent(Event):
    container_name: str
    old_status: str
    new_status: str
```

### 2.2. Paso 2: Crear el Hook

Cree un nuevo fichero [`src/hooks/container_health_restart.py`](src/hooks/container_health_restart.py) para el hook. Este fichero contendrá la lógica para suscribirse al evento `ContainerHealthChangedEvent` y reiniciar el contenedor si su estado de salud cambia a "unhealthy".

```python
import asyncio
import logging
from src.hooks.core.events import EventBus, EventFilter
from src.hooks.events.container_health import ContainerHealthChangedEvent
from src.hooks.core.config import ContainerMonitorConfig

class ContainerHealthRestartHook:
    def __init__(self, event_bus: EventBus, config: ContainerMonitorConfig):
        self.event_bus = event_bus
        self.config = config
        self.logger = logging.getLogger(__name__)

    async def start(self):
        self.event_bus.subscribe(
            self.handle_container_health_changed,
            EventFilter(event_types=[ContainerHealthChangedEvent.__name__])
        )
        self.logger.info("ContainerHealthRestartHook started")

    async def handle_container_health_changed(self, event: ContainerHealthChangedEvent):
        if event.new_status == "unhealthy":
            self.logger.warning(f"Container {event.container_name} is unhealthy, restarting...")
            # TODO: Implement container restart logic here
            # This would likely involve using the Podman/Docker API
            await asyncio.sleep(5) # Simulate restart
            self.logger.info(f"Container {event.container_name} restarted")

    async def stop(self):
        # TODO: Implement unsubscription logic
        self.logger.info("ContainerHealthRestartHook stopped")
```

### 2.3. Paso 3: Integrar con el Bus de Eventos

Modifique el fichero [`src/hooks/register_refactor_hook.py`](src/hooks/register_refactor_hook.py) para registrar el nuevo hook en el bus de eventos.

```python
# TODO: Implement hook registration logic here
```

### 2.4. Paso 4: Eliminar el Código Antiguo

Elimine la lógica relacionada con el `Container Health Restart Hook` de la clase `KiroAgentHooks` en [`src/phoenix_system_review/automation/kiro_hooks.py`](src/phoenix_system_review/automation/kiro_hooks.py).

### 2.5. Paso 5: Configuración

Asegúrese de que el nuevo hook pueda ser configurado a través del sistema de configuración centralizado ([`src/hooks/core/config.py`](src/hooks/core/config.py)).

## 3. Consideraciones Adicionales

*   **Pruebas:** Implementar pruebas unitarias y de integración para cada hook migrado.
*   **Documentación:** Actualizar la documentación para reflejar la nueva arquitectura.
*   **Manejo de Errores:** Implementar un manejo de errores robusto para garantizar la estabilidad del sistema.

## 4. Conclusión

Este documento proporciona un plan detallado para migrar los Agent Hooks a la nueva arquitectura. Siguiendo esta guía, el equipo de desarrollo puede migrar los hooks restantes de manera eficiente y consistente.