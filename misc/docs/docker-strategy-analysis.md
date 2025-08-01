# Análisis y Estrategia de Contenedores

Este documento describe la estrategia de contenedores del proyecto, analiza sus componentes actuales, propone un plan de optimización y proporciona una guía para los desarrolladores.

## 1. Visión General de la Estrategia Actual

La estrategia de contenedores se basa en Docker y está dividida en dos entornos principales: desarrollo y producción.

-   **Entorno de Desarrollo:** Utiliza `docker-compose` para orquestar los servicios. Actualmente, existen dos archivos (`compose.yaml` y `docker-compose.yml`), lo que genera confusión. La intención es facilitar un entorno local para pruebas y desarrollo.
-   **Entorno de Producción:** Utiliza `docker-compose.prod.yml` con sintaxis de `deploy`, diseñado para un clúster de Docker Swarm. Este archivo gestiona los servicios de infraestructura como bases de datos y herramientas de orquestación.

Cada agente principal (`chaos`, `demigod`, `thanatos`) tiene su propio `Dockerfile`, que sigue un patrón de **construcción multi-etapa (multi-stage build)** para optimizar el tamaño y la seguridad de las imágenes.

## 2. Análisis de los Artefactos Docker

### 2.1. Dockerfiles (`Dockerfile.chaos`, `Dockerfile.demigod`, `Dockerfile.thanatos`)

Los `Dockerfile` para los agentes son el pilar de la estrategia de imágenes.

**Puntos Fuertes:**

-   **Multi-Stage Builds:** Separan eficazmente el entorno de construcción del de ejecución, resultando en imágenes finales más pequeñas y seguras.
-   **Seguridad:** Crean y utilizan un **usuario no-root (`appuser`)**, una práctica de seguridad esencial para mitigar riesgos.
-   **Optimización de Capas:** Aprovechan el cacheo de capas de Docker al instalar las dependencias de `requirements.txt` antes de copiar el código fuente.
-   **Imágenes Base Ligeras:** Usan `python:3.10-slim` como base, reduciendo la superficie de ataque y el tamaño de la imagen.

**Puntos de Mejora y Recomendaciones:**

-   **Consistencia y Redundancia:** Los tres `Dockerfile` son casi idénticos.
    -   **Propuesta:** Unificar los tres archivos en un único `Dockerfile.agent.base` y usar argumentos de construcción (`ARG`) para especificar el script de `CMD` de cada agente. Esto reduce la duplicación y simplifica el mantenimiento.
-   **Copia de Archivos:** Se copia el directorio `src` completo (`COPY ../../src/. /app/src/`).
    -   **Propuesta:** Implementar un archivo `.dockerignore` en el directorio raíz del proyecto para excluir archivos innecesarios (ej. `__pycache__`, `tests/`, archivos de configuración local). Esto reduce el contexto de construcción y previene la fuga de información sensible.
-   **Comando de Inicio (CMD):** El `CMD` utiliza una ruta absoluta.
    -   **Propuesta:** Aunque funcional, se recomienda hacer el `WORKDIR` el directorio desde donde se ejecutan los comandos para simplificar la instrucción `CMD` (ej. `CMD ["python", "src/core/demigod-agent.py"]`).

### 2.2. Archivos de Orquestación

**Entorno de Desarrollo (`compose.yaml` y `docker-compose.yml`)**

-   **Confusión:** Existen dos archivos, `compose.yaml` y `docker-compose.yml`, con contenido parcialmente superpuesto. `compose.yaml` es más completo (incluye `healthchecks` y servicios de terceros como `windmill`), mientras que `docker-compose.yml` solo define los agentes.
    -   **Propuesta:** Fusionar ambos archivos en un único `docker-compose.yml` que sirva como la única fuente de verdad para el entorno de desarrollo. Este archivo debería incluir todos los servicios (agentes, bases de datos, etc.) y sus configuraciones de `build`.
-   **Experiencia de Desarrollador:**
    -   **Propuesta:** El `docker-compose.yml` unificado debe incluir la sección `build` para cada agente, permitiendo a los desarrolladores levantar todo el entorno con un solo comando (`docker-compose up --build`) sin necesidad de construir las imágenes previamente.
    -   **Propuesta:** Revisar el uso de volúmenes. Montar todo el proyecto (`../../..:/app`) es útil para el desarrollo, pero se debe asegurar que el `.dockerignore` esté bien configurado para evitar problemas de rendimiento y consistencia.

**Entorno de Producción (`docker-compose.prod.yml`)**

-   **Puntos Fuertes:**
    -   Usa la sintaxis de `deploy` para Docker Swarm.
    -   Utiliza volúmenes nombrados para la persistencia de datos.
-   **Vulnerabilidades Críticas y Malas Prácticas:**
    -   **Secretos Hardcodeados:** Las contraseñas de la base de datos están escritas directamente en el archivo. **Esto es un riesgo de seguridad grave.**
        -   **Propuesta:** Utilizar **Docker Secrets** para gestionar todas las credenciales y claves de API. Los secretos se montan en los contenedores como archivos y se leen desde variables de entorno.
    -   **Etiquetas de Imagen:** Se utiliza la etiqueta `:latest` para las imágenes.
        -   **Propuesta:** Implementar una política de etiquetado de imágenes inmutable. Usar versiones semánticas o el hash del commit de Git (ej. `mi-agente:1.2.4` o `mi-agente:sha-a1b2c3d`). Esto garantiza despliegues reproducibles y facilita los rollbacks.

## 3. Plan de Optimización Propuesto

1.  **Unificar Dockerfiles:** Refactorizar los tres `Dockerfile` de los agentes en un único `Dockerfile.agent.base` parametrizado.
2.  **Implementar `.dockerignore`:** Crear un archivo `.dockerignore` completo en la raíz del proyecto.
3.  **Consolidar Compose de Desarrollo:** Fusionar `compose.yaml` y `docker-compose.yml` en un solo `docker-compose.yml`, que incluya la sección `build` para todos los agentes.
4.  **Securizar Compose de Producción:** Migrar todas las credenciales hardcodeadas en `docker-compose.prod.yml` a **Docker Secrets**.
5.  **Política de Etiquetado de Imágenes:** Dejar de usar la etiqueta `:latest` en producción y adoptar un sistema de versionado inmutable.
6.  **Crear `.env.example`:** Añadir un archivo `.env.example` al repositorio para que los desarrolladores sepan qué variables de entorno configurar para el entorno local.

## 4. Guía de Uso para Desarrolladores

Para levantar el entorno de desarrollo local, sigue estos pasos:

1.  **Configurar Variables de Entorno:**
    Copia el archivo `.env.example` a un nuevo archivo llamado `.env` y rellena las variables necesarias.

    ```bash
    cp .env.example .env
    # Edita el archivo .env con tus valores
    ```

2.  **Levantar el Entorno:**
    Desde la raíz del proyecto, ejecuta el siguiente comando. Esto construirá las imágenes de los agentes (si no existen o si el `Dockerfile` ha cambiado) y levantará todos los servicios definidos.

    ```bash
    docker-compose -f BooPhoenix369/docker/docker-compose.yml up --build
    ```

3.  **Detener el Entorno:**
    Para detener y eliminar los contenedores, ejecuta:

    ```bash
    docker-compose -f BooPhoenix369/docker/docker-compose.yml down
