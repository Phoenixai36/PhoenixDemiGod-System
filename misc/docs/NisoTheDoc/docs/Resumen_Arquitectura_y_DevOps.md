# Resumen de Arquitectura y Estrategia DevOps – Phoenix DemiGod v8.7

Tras analizar los documentos proporcionados, se extrae la siguiente síntesis de la arquitectura y estrategia DevOps del proyecto:

## 1. Principios Arquitectónicos Fundamentales:

*   **"Células Madre Digitales":** El concepto central es una arquitectura base que puede "especializarse" o "diferenciarse" dinámicamente para adaptarse a cualquier vertical de negocio (ej. entretenimiento, industria 4.0, marketing) sin necesidad de reestructurar el núcleo. Posee mecanismos de "memoria genética" para transferir aprendizajes entre especializaciones y "regeneración" para recuperarse de fallos.
*   **Malla de Micro-servicios AI:** La plataforma no es un monolito, sino un conjunto de servicios interconectados. El núcleo se centra en modelos de IA sin Transformers (Mamba/SSM, RWKV) por su eficiencia computacional (complejidad lineal O(n)) y menor consumo energético.
*   **Arquitectura Agnóstica al Modelo y al Proveedor:** El sistema está diseñado para no depender de un único proveedor de modelos o de nube (anti-vendor lock-in), utilizando estándares abiertos como OCI y protocolos de comunicación universales (MCP) para integrar fácilmente nuevas tecnologías.

## 2. Stack Tecnológico Principal:

*   **Inferencia y Modelos:**
    *   **Modelos Base:** Principalmente arquitecturas sin Transformers como Mamba, Zamba2, RWKV, y Falcon-Mamba, cuantizados en formato GGUF para optimizar el rendimiento.
    *   **Runtimes de Inferencia:** `llama.cpp` para ejecución eficiente, y `vLLM` como "sidecar" para servir múltiples modelos de forma concurrente a través de una API.
*   **Orquestación y Automatización:**
    *   **Windmill:** Orquestador principal para flujos de trabajo complejos y scripts (Python/TypeScript), especialmente en el pipeline de CI/CD.
    *   **n8n:** Plataforma de bajo código para automatizar integraciones, notificaciones y workflows más sencillos o disparados por eventos.
*   **Observabilidad:**
    *   **Prometheus:** Recolección de métricas clave (latencia p95, uso de GPU, tasa de errores).
    *   **Grafana:** Visualización de métricas en dashboards.
    *   **Loki:** Centralización de logs estructurados.
    *   **Alertmanager:** Gestión de alertas (ej. notificaciones a PagerDuty).

## 3. Pipeline de CI/CD (Enfoque GitOps):

*   **Control de Versiones:** Un monorepo en GitHub es la única fuente de verdad. El estado deseado de la infraestructura, los modelos y las aplicaciones se declara en el repositorio.
*   **Integración Continua (CI):**
    *   GitHub Actions se activa con cada Pull Request a la rama `main`.
    *   Los workflows ejecutan validaciones como linting, pruebas unitarias y benchmarks de regresión de modelos.
    *   Se construyen imágenes de contenedor OCI con `Podman-build` y se firman con `cosign`.
    *   Las imágenes se publican en un registro privado Harbor.
*   **Entrega Continua (CD):**
    *   Windmill detecta las nuevas imágenes en Harbor y dispara la actualización.
    *   Aplica los manifiestos de Terraform para actualizar la infraestructura.
    *   Utiliza una estrategia de despliegue "Canary" para liberar nuevas versiones de forma gradual y minimizar riesgos.
    *   n8n ejecuta pruebas de humo post-despliegue y notifica los resultados.

## 4. Enfoque de Contenedores (Podman):

*   **Justificación:** Se prefiere Podman sobre Docker principalmente por seguridad. Al operar en modo `rootless` por defecto, reduce significativamente la superficie de ataque, ya que no requiere un demonio con privilegios de superusuario. Además, se integra de forma más nativa con `systemd` para gestionar los contenedores como servicios del sistema.

## 5. Infraestructura como Código (IaC):

*   **Herramienta:** Terraform se utiliza para gestionar de forma declarativa todos los recursos de la infraestructura, incluyendo nodos de computación, volúmenes de almacenamiento (ZFS) y configuración de red.
*   **Gestión de Entornos:** El código de Terraform está modularizado para gestionar diferentes componentes (routers, modelos, etc.) y se utilizan etiquetas de Git (`phase-1`, `phase-2`) para controlar y evitar desviaciones (drift) entre los entornos de desarrollo, staging y producción.