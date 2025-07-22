 e# Plan de Refactorización de Hooks

Este documento detalla el plan para migrar los hooks existentes en `src/agent_hooks/hooks` a la nueva arquitectura de `AgentHook` en `.kiro/engine`.

---

## 1. automated_test_runner_hook.py

-   **Nombre del Fichero:** `src/agent_hooks/hooks/automated_test_runner_hook.py`
-   **Propósito:** Ejecuta tests automáticamente cuando se modifican, crean o renombran ficheros de código.
-   **Lógica de Disparo (Trigger):**
    -   `EventType.FILE_SAVE`
    -   `EventType.FILE_MODIFY`
    -   `EventType.FILE_CREATE`
    -   `EventType.FILE_RENAME`
-   **Condiciones de Filtro (EventFilterGroup):**
    -   Un filtro para la extensión del fichero, que coincida con los `file_patterns` (p. ej., `*.py`).
    -   Un filtro para excluir ficheros que coincidan con `exclude_patterns` (p. ej., `__pycache__/*`).
    -   La lógica de "debounce" deberá ser manejada internamente por el hook, ya que depende del estado (última ejecución por módulo).

---

## 2. cellular_communication_hook.py

-   **Nombre del Fichero:** `src/agent_hooks/hooks/cellular_communication_hook.py`
-   **Propósito:** Monitoriza y gestiona el protocolo de comunicación intercelular (CCP) del sistema PHOENIXxHYDRA.
-   **Lógica de Disparo (Trigger):**
    -   `EventType.CUSTOM`
-   **Condiciones de Filtro (EventFilterGroup):**
    -   Un filtro por el nombre del evento personalizado (`event_name`). Debería reaccionar a:
        -   `ccp_message_sent`
        -   `ccp_message_received`
        -   `ccp_security_alert`
    -   Esto se puede modelar con un `EventFilter` que compruebe `event.name` dentro de un `EventFilterGroup`.

---

## 3. container_health_restart_hook.py

-   **Nombre del Fichero:** `src/agent_hooks/hooks/container_health_restart_hook.py`
-   **Propósito:** Reinicia automáticamente contenedores que se reportan como no saludables.
-   **Lógica de Disparo (Trigger):**
    -   `EventType.SERVICE_HEALTH`
-   **Condiciones de Filtro (EventFilterGroup):**
    -   Filtro por el campo `component` del evento, que debe empezar con `container:`.
    -   Filtro por el campo `status` del evento, que debe estar en la lista `["unhealthy", "failed", "error", "critical"]`.
    -   La lógica de exclusión (`excluded_containers`), reintentos (`max_restart_attempts`) y cooldown (`restart_cooldown_seconds`) deberá ser manejada internamente por el hook, ya que depende del estado.

---

## 4. container_log_analysis_hook.py

-   **Nombre del Fichero:** `src/agent_hooks/hooks/container_log_analysis_hook.py`
-   **Propósito:** Analiza logs de contenedores en busca de patrones de error y ejecuta acciones de remediación.
-   **Lógica de Disparo (Trigger):**
    -   `EventType.CUSTOM` con el nombre `container_log`.
-   **Condiciones de Filtro (EventFilterGroup):**
    -   Filtro por el nombre del evento personalizado (`event_name`), que debe ser `container_log`.
    -   La lógica de exclusión (`excluded_containers`) y el intervalo de análisis (`analysis_interval_seconds`) se manejarán internamente. El análisis de patrones sobre el contenido de los logs también es lógica interna del hook.

---

## 5. container_resource_scaling_hook.py

-   **Nombre del Fichero:** `src/agent_hooks/hooks/container_resource_scaling_hook.py`
-   **Propósito:** Escala los recursos de los contenedores (CPU, memoria) basándose en métricas de uso.
-   **Lógica de Disparo (Trigger):**
    -   `EventType.RESOURCE_USAGE`
-   **Condiciones de Filtro (EventFilterGroup):**
    -   Filtro por el campo `metric_name` del evento, que debe empezar con `container.`.
    -   La lógica de exclusión (`excluded_containers`), cooldown (`scaling_cooldown_seconds`), y la evaluación de umbrales sobre las métricas acumuladas son parte de la lógica interna del hook.

---

## 6. example_hook.py

-   **Nombre del Fichero:** `src/agent_hooks/hooks/example_hook.py`
-   **Propósito:** Un hook de ejemplo para demostrar la funcionalidad básica.
-   **Lógica de Disparo (Trigger):**
    -   Depende de la configuración (`self.triggers`), pero podría ser cualquier `EventType`.
-   **Condiciones de Filtro (EventFilterGroup):**
    -   Un filtro genérico que compruebe si el `event.type` está en la lista de triggers configurados para el hook.