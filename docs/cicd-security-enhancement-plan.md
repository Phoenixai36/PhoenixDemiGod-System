# Plan de Mejora de Seguridad para el Pipeline de CI/CD

Este documento detalla el plan para integrar un escáner de seguridad automatizado en el pipeline de CI/CD existente, con el objetivo de añadir una capa de seguridad proactiva.

## 1. Herramienta Seleccionada y Justificación

**Herramienta:** [GitHub CodeQL](https://codeql.github.com/)

**Justificación:**

*   **Integración Nativa:** CodeQL es una herramienta desarrollada y mantenida por GitHub, lo que garantiza una integración perfecta y simplificada con GitHub Actions. Se puede configurar con unas pocas líneas de YAML.
*   **Análisis Estático Potente (SAST):** Se especializa en el análisis de código fuente para detectar vulnerabilidades de seguridad, como inyecciones de SQL, desbordamientos de búfer y vulnerabilidades de scripting entre sitios (XSS), entre otras. Esto complementa las verificaciones de formato y `linting` ya existentes.
*   **Soporte para Rust:** CodeQL tiene un excelente soporte para el lenguaje Rust, lo que permite un análisis profundo y preciso del código del proyecto.
*   **Sin Coste para Proyectos Públicos:** Es gratuito para repositorios de código abierto, lo que lo hace ideal para este contexto.
*   **Flujo de Trabajo Eficiente:** Los resultados se muestran directamente en la pestaña "Security" del repositorio y pueden bloquear `pull requests` si se detectan vulnerabilidades críticas, forzando un enfoque de "seguridad por defecto".

## 2. Estrategia de Integración

La integración se realizará añadiendo un nuevo `job` al pipeline de CI/CD llamado `security-scan`. Este `job` se ejecutará en paralelo a los trabajos existentes (`format`, `lint`, `test`) para no incrementar el tiempo total de ejecución del pipeline.

El `job` realizará los siguientes pasos:
1.  **Checkout del código:** Descargará el código del repositorio.
2.  **Inicialización de CodeQL:** Configurará el entorno de análisis de CodeQL, generando una base de datos del código fuente para su posterior análisis.
3.  **Autobuild (si es necesario):** Para lenguajes compilados como Rust, CodeQL intentará construir el código para obtener una representación más precisa.
4.  **Análisis con CodeQL:** Ejecutará las consultas de seguridad predefinidas sobre la base de datos de código.
5.  **Subida de resultados:** Los resultados se cargarán a GitHub para ser visualizados en la interfaz de seguridad.

## 3. Propuesta de Modificación del Pipeline

A continuación se muestra el fragmento de código YAML que debe añadirse al archivo `BooPhoenix369/ci.yml`. Se recomienda colocarlo después del `job` de `test`.

```yaml
# ... (jobs existentes: format, lint, test)

  security-scan:
    name: Escaneo de Seguridad (CodeQL)
    runs-on: ubuntu-latest
    permissions:
      security-events: write # Permiso necesario para que CodeQL suba los resultados
      actions: read # Permiso para que el action pueda leer metadata del workflow

    steps:
      - name: Checkout del repositorio
        uses: actions/checkout@v3

      # Inicializa el escáner de CodeQL.
      # Genera una base de datos del código para analizar.
      - name: Inicializar CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: rust # Especifica el lenguaje a analizar

      # Para lenguajes compilados, CodeQL necesita observar el proceso de build.
      # Este paso compila el código para que CodeQL pueda analizarlo.
      # Se añade cacheo para acelerar el proceso.
      - name: Cacheo de dependencias de Rust
        uses: actions/cache@v3
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v2

      # Ejecuta el análisis de CodeQL sobre la base de datos generada.
      - name: Realizar análisis con CodeQL
        uses: github/codeql-action/analyze@v2
```

## 4. Configuración Adicional

*   **Permisos del Workflow:** Es crucial añadir la sección `permissions` al `job` (o a nivel de workflow) para permitir que la acción de CodeQL escriba los resultados en la pestaña de seguridad de GitHub. La propuesta de YAML ya incluye los permisos necesarios a nivel de `job`.
*   **No se requieren tokens:** Para la configuración básica en un repositorio de GitHub, no es necesario gestionar secretos o tokens de API, lo que simplifica la configuración.