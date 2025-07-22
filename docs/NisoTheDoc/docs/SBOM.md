# Software Bill of Materials (SBOM)

## Resumen Ejecutivo

Este documento proporciona una lista consolidada de todas las dependencias de software utilizadas en el proyecto Phoenix DemiGod. El objetivo es mantener un inventario claro y actualizado de todos los componentes de terceros, diferenciando entre dependencias de producción y de desarrollo para facilitar la gestión de seguridad, licencias y versiones.

## Dependencias Python (Producción)

Lista consolidada de todas las dependencias de Python necesarias para que el proyecto funcione en un entorno de producción.

- autogen==0.4.0
- fastapi==0.115.0
- keras==3.5.0
- librosa
- matplotlib
- numpy
- openai==1.47.0
- pandas
- podman-compose
- pydantic
- pydub
- pymongo
- python-dotenv
- rasa==3.6.0
- rasa-sdk
- redis
- scikit-learn
- torch
- typer==0.12.5
- uvicorn==0.30.6

## Dependencias Python (Desarrollo)

Lista de dependencias adicionales utilizadas para el desarrollo, pruebas y formateo de código.

- flake8
- httpx
- pre-commit==3.8.0
- pytest
- pytest-cov
- ruff==0.6.9

## Dependencias Node.js

Lista consolidada de dependencias de Node.js.

- @genkit-ai/mcp: ^1.14.1-rc.1

## Análisis y Recomendaciones

Durante el análisis de las dependencias, se han identificado las siguientes observaciones:

*   **Conflictos de Versión en `numpy`:** Se han encontrado múltiples especificaciones de versión para `numpy`.
    *   `BooPhoenix369/docker/agent-requirements.txt` especifica `numpy==1.24.4`.
    *   `BooPhoenix369/requirements.txt` y `BooPhoenix369/docker/demigod-requirements.txt` especifican `numpy>=1.26.4`.
    *   El `requirements.txt` raíz no especifica versión.
    *   **Recomendación:** Unificar la versión de `numpy` en todos los archivos para evitar comportamientos inesperados. Se recomienda usar la versión más reciente que sea compatible con todas las demás librerías.

*   **Conflictos de Versión en `pydantic`:** Se han encontrado dos versiones diferentes de `pydantic`.
    *   `BooPhoenix369/docker/agent-requirements.txt` especifica `pydantic==1.10.2`.
    *   `BooPhoenix369/requirements.txt` y `BooPhoenix369/docker/demigod-requirements.txt` especifican `pydantic==2.9.2`.
    *   **Recomendación:** `Pydantic` v1 y v2 tienen cambios significativos en la API. Es crucial determinar qué partes del sistema dependen de cada versión y planificar una migración a una única versión (preferiblemente v2) para evitar conflictos.

*   **Dependencias Duplicadas de Node.js:** La dependencia `@genkit-ai/mcp` está declarada en tres archivos `package.json` diferentes con la misma versión.
    *   `package.json`
    *   `BooPhoenix369/package.json`
    *   `BooPhoenix369/Niso/package.json`
    *   **Recomendación:** Considerar la posibilidad de gestionar las dependencias de Node.js desde un único archivo `package.json` en la raíz del proyecto si la estructura del monorepo lo permite, utilizando workspaces para simplificar la gestión.

*   **Dependencias de Desarrollo Mezcladas:** Algunas dependencias de desarrollo como `pytest`, `ruff` y `pre-commit` están listadas en archivos de requerimientos de producción (`requirements.txt`).
    *   **Recomendación:** Mover todas las dependencias de desarrollo a `requirements-dev.txt` para mantener una clara separación entre los entornos de producción y desarrollo.