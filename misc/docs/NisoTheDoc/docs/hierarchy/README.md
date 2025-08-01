# Sistema de Jerarquía y Gobierno de Agentes

La robustez y coherencia del sistema Phoenix DemiGod se basan en un sistema de gobierno explícito que define cómo los agentes interactúan, colaboran y se gestionan a sí mismos. Este sistema se define de manera declarativa a través de archivos de configuración YAML, lo que permite una fácil modificación y auditoría de las reglas del sistema.

La configuración de la jerarquía se encuentra principalmente en el directorio [`config/hierarchy/`](../../config/hierarchy/).

---

### 1. Protocolos de Comunicación (`communication-protocols.yaml`)

Este archivo define las reglas y formatos para el intercambio de mensajes entre agentes. Su objetivo es estandarizar la comunicación para garantizar que los mensajes sean interpretables y procesables por cualquier agente del sistema.

**Conceptos Clave:**

-   **Tipos de Mensajes:** Define los tipos de mensajes permitidos (ej. `TASK_ASSIGN`, `STATUS_UPDATE`, `DATA_REQUEST`, `RESULT_DELIVERY`).
-   **Esquema del Mensaje:** Especifica la estructura obligatoria de cada mensaje, que generalmente incluye:
    -   `sender_id`: Identificador del agente emisor.
    -   `receiver_id`: Identificador del agente receptor (puede ser un broadcast).
    -   `message_type`: El tipo de mensaje según la lista definida.
    -   `payload`: Los datos relevantes para el mensaje.
    -   `timestamp`: Marca de tiempo de la creación del mensaje.
-   **Canales de Comunicación:** Define los canales (ej. `high_priority`, `general_bus`, `logging`) por los que pueden fluir los mensajes, permitiendo la priorización del tráfico.

### 2. Estrategias de Consenso (`consensus-strategies.yaml`)

Para tareas que requieren la colaboración de múltiples agentes o la toma de decisiones colectivas, este archivo define los mecanismos de consenso que se deben utilizar.

**Estrategias Implementadas:**

-   **Votación Mayoritaria (Majority Voting):** La opción más simple, donde una decisión se toma si supera el 50% de los votos de los agentes involucrados.
-   **Consenso Ponderado (Weighted Consensus):** Ciertos agentes (ej. `God-Agent` de la capa cognitiva) tienen un mayor peso en la votación, lo que refleja su importancia estratégica en la jerarquía.
-   **Prueba de Autoridad (Proof-of-Authority):** Para decisiones críticas, solo un conjunto predefinido de agentes de alto nivel puede validar una propuesta.

La estrategia a utilizar se especifica en la asignación de la tarea, permitiendo flexibilidad según la naturaleza del problema.

### 3. Reglas de Renacimiento (`rebirth-rules.yaml`)

Este es uno de los componentes más críticos para la resiliencia del sistema. Define el protocolo de "muerte y renacimiento" que permite al sistema auto-sanarse.

**Funcionamiento:**

1.  **Detección de Fallos (Health Checks):** El `Monitoring-Agent` realiza chequeos de salud periódicos a todos los demás agentes.
2.  **Declaración de "Muerte":** Si un agente no responde o reporta un estado irrecuperable, el `Monitoring-Agent` lo declara como "muerto" y notifica al `Healer-Agent`.
3.  **Aislamiento:** El agente fallido es aislado de la red para evitar que propague errores.
4.  **Análisis Post-Mortem:** El `Thanatos-Agent` puede ser invocado para analizar los últimos logs y el estado del agente fallido, generando un informe de la causa raíz.
5.  **Renacimiento (Rebirth):** El `Healer-Agent`, siguiendo las reglas de este archivo, reinicia el agente a partir de su configuración inicial o de un punto de control guardado, restaurando su estado y reintegrándolo a la red.

Este mecanismo garantiza que el sistema pueda recuperarse de fallos inesperados en agentes individuales sin necesidad de una intervención manual, asegurando una operación continua y robusta.