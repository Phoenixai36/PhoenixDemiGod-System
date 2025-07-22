# Guía de OMAS

## Propósito
OMAS (Orchestration, Management, and Automation System) es el componente central encargado de la coordinación y gestión de los agentes dentro del sistema Phoenix Demigod. Su función principal es asegurar que los agentes operen de manera cohesiva y eficiente, respondiendo dinámicamente a los eventos del sistema y a las decisiones basadas en reglas.

## Componentes Clave
- **Agentes**: OMAS interactúa con varios agentes, como `demigod-agent`, `chaos-agent` y `thanatos-agent`, orquestando sus acciones y flujos de trabajo.
- **Reglas de Decisión**: Utiliza un motor de reglas para tomar decisiones dinámicas basadas en el estado del sistema y los objetivos predefinidos. Estas reglas se definen en el directorio `omas/rules/`.
- **Configuraciones**: Las configuraciones específicas de cada agente y del propio OMAS se gestionan a través de archivos YAML ubicados en `omas/configs/` y `omas/agents/`.

## Configuración
Para configurar OMAS y sus agentes, sigue estos pasos:

1.  **Configuración de Agentes**:
    Los archivos de configuración para cada agente se encuentran en `omas/agents/`. Cada archivo YAML define el comportamiento, los endpoints y las dependencias del agente. Asegúrate de personalizar los siguientes campos:
    -   `endpoint`: La URL donde el agente está accesible.
    -   `rules_file`: El archivo de reglas específico que el agente debe cargar.
    -   `log_file`: La ruta del archivo de log del agente.

    Ejemplo de configuración de `demigod-agent.yaml`:
    ```yaml
    agent_name: demigod
    endpoint: http://localhost:8001/demigod
    rules_file: omas/rules/demigod-decision.rules
    log_file: omas/logs/demigod-agent.log
    ```

2.  **Configuración Global de OMAS**:
    El archivo `omas/configs/omas-config.yaml` contiene la configuración global de OMAS, incluyendo la lista de agentes a cargar y la configuración del motor de reglas.

3.  **Definición de Reglas**:
    Las reglas de decisión se definen en archivos `.rules` dentro de `omas/rules/`. Estas reglas utilizan un formato específico para dictar cómo OMAS debe responder a diferentes escenarios.

## Uso
OMAS se inicia automáticamente como parte del sistema Phoenix Demigod. Una vez en funcionamiento, monitorea el estado de los agentes y aplica las reglas de decisión para mantener la estabilidad y eficiencia del sistema.

Para ver los logs de OMAS y sus agentes, consulta los archivos en `omas/logs/`.