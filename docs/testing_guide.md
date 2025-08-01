# Guía de Pruebas

## 1. Introducción

Esta guía proporciona información sobre cómo escribir y ejecutar pruebas unitarias y de integración para el proyecto Phoenix Hydra.

## 2. Pruebas Unitarias

Las pruebas unitarias verifican que las unidades individuales de código (por ejemplo, funciones, clases, módulos) funcionen correctamente.

### 2.1. Cómo Escribir Pruebas Unitarias

1.  Utilice el framework de pruebas `pytest`.
2.  Escriba pruebas para cada unidad de código.
3.  Utilice aserciones para verificar que el código se comporta como se espera.
4.  Aísle las pruebas unitarias de las dependencias externas (por ejemplo, bases de datos, APIs).

### 2.2. Ejemplos de Pruebas Unitarias

```python
# tests/unit/event_routing/test_event_store.py
import pytest
from src.event_routing.event_store import EventStore

def test_event_store_store_and_get():
    event_store = EventStore()
    event = {"id": "1", "type": "test"}
    event_store.store(event)
    retrieved_event = event_store.get_event_by_id("1")
    assert retrieved_event == event
```

## 3. Pruebas de Integración

Las pruebas de integración verifican que los diferentes componentes del sistema funcionen correctamente juntos.

### 3.1. Cómo Escribir Pruebas de Integración

1.  Utilice el framework de pruebas `pytest`.
2.  Escriba pruebas que involucren a varios componentes del sistema.
3.  Utilice aserciones para verificar que los componentes interactúan correctamente.
4.  Utilice entornos de prueba para simular el entorno de producción.

### 3.2. Ejemplos de Pruebas de Integración

```python
# tests/integration/test_event_routing.py
import pytest
from src.event_routing.event_router import EventRouter
from src.event_routing.event_store import EventStore

def test_event_router_store_and_route():
    event_router = EventRouter()
    event_store = EventStore()
    event_router.event_store = event_store
    event = {"id": "1", "type": "test"}
    event_router.publish(event)
    retrieved_event = event_store.get_event_by_id("1")
    assert retrieved_event == event
```

## 4. Ejecución de las Pruebas

Para ejecutar las pruebas, utilice el siguiente comando:

```bash
pytest
```

## 5. Conclusión

Esta guía proporciona información sobre cómo escribir y ejecutar pruebas unitarias y de integración para el proyecto Phoenix Hydra.