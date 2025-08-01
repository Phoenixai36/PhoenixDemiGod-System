# Plan de Refactorización de Dependencias

## 1. Objetivos

El objetivo principal de este plan es refactorizar y unificar la gestión de dependencias del proyecto Phoenix DemiGod para lograr los siguientes resultados:

* **Unificación:** Consolidar la declaración de dependencias para evitar conflictos y duplicaciones.
* **Claridad:** Separar estrictamente las dependencias de producción de las de desarrollo.
* **Mantenibilidad:** Simplificar el proceso de actualización y gestión de las dependencias a largo plazo.
* **Reproducibilidad:** Asegurar que los entornos de desarrollo y producción se construyan con versiones de paquetes idénticas y predecibles.

## 2. Estrategia Propuesta

### 2.1. Gestión de Dependencias Python

Se recomienda adoptar **`pip-tools`** para la gestión de las dependencias de Python.

* **Justificación:** `pip-tools` ofrece un excelente equilibrio entre simplicidad y potencia. Permite definir las dependencias de alto nivel en archivos `.in` y compila archivos `.txt` con todas las versiones "pineadas" (bloqueadas). Esto resuelve los problemas de conflictos de versiones y asegura builds reproducibles sin introducir la complejidad de un sistema de gestión de paquetes completo como Poetry, lo que facilita una adopción más rápida.

* **Nueva Estructura de Archivos:**
  * `requirements.in`: Contendrá las dependencias directas de producción (ej. `fastapi`, `torch`).
  * `requirements-dev.in`: Contendrá las dependencias de desarrollo (ej. `pytest`, `ruff`).
  * `requirements.txt`: Será generado por `pip-compile` a partir de `requirements.in`. **Este será el único archivo usado en producción.**
  * `requirements-dev.txt`: Será generado por `pip-compile` a partir de `requirements-dev.in`.

### 2.2. Gestión de Dependencias Node.js

Se recomienda utilizar la funcionalidad de **`npm workspaces`** (o `yarn workspaces`).

* **Justificación:** Es el estándar de la industria para gestionar monorepos. Permite centralizar todas las dependencias en un único archivo `package.json` en la raíz, eliminando la duplicación y simplificando las actualizaciones.

## 3. Pasos de Implementación

1. **Crear Rama de Trabajo:** Aislar todos los cambios en una nueva rama.

```bash
git checkout -b feature/dependency-refactor
```

2. **Implementar `pip-tools` (Python):**
  * Instalar `pip-tools`: `pip install pip-tools`.
  * Crear `requirements.in` en la raíz del proyecto con las dependencias de producción unificadas, resolviendo los conflictos de `numpy` y `pydantic` (se optará por la versión más reciente compatible).
  * Crear `requirements-dev.in` en la raíz con las dependencias de desarrollo.
  * Generar los archivos de requerimientos bloqueados:

```bash
pip-compile requirements.in -o requirements.txt
pip-compile requirements-dev.in -o requirements-dev.txt
```

3. **Limpiar Archivos Antiguos:** Eliminar todos los archivos `requirements.txt` y `requirements-dev.txt` de los subdirectorios (`BooPhoenix369/`, `BooPhoenix369/docker/`, etc.).

4. **Actualizar Dockerfiles:** Modificar todos los `Dockerfile` para que copien y utilicen los nuevos archivos `requirements.txt` y `requirements-dev.txt` desde la raíz del proyecto.

5. **Actualizar Scripts de CI/CD:** Revisar y modificar los scripts de integración continua (ej. `BooPhoenix369/ci.yml`) para que utilicen los nuevos comandos de instalación: `pip install -r requirements.txt`.

6. **Refactorizar Dependencias Node.js:**
  * Configurar `workspaces` en el `package.json` de la raíz.
  * Mover las dependencias de los `package.json` anidados al `package.json` principal.

7. **Verificación y Pruebas:**
  * Construir todas las imágenes de Docker localmente para asegurar que el proceso de instalación de dependencias funciona correctamente.
  * Ejecutar la suite completa de pruebas (unitarias, integración) para verificar que no se ha introducido ninguna regresión.

8. **Crear Pull Request:** Enviar los cambios para revisión del equipo.

## 4. Análisis de Riesgos y Mitigación

* **Riesgo:** Ruptura del build o fallos en tiempo de ejecución debido a incompatibilidades de versión (especialmente con `pydantic` v1 vs. v2).
    *   **Mitigación:**
    1. Realizar todos los cambios en una rama de características aislada.
    2. Realizar pruebas exhaustivas antes de fusionar.
    3. El plan de implementación debe incluir una decisión explícita sobre la versión de `pydantic` a utilizar, documentando cualquier cambio necesario en el código para adaptarse a la API de la versión elegida.

* **Riesgo:** La configuración de CI/CD o los scripts de despliegue pueden fallar si no se actualizan correctamente.
  * **Mitigación:** Identificar y actualizar todos los scripts que hagan referencia a los antiguos archivos de dependencias. Probar el pipeline de CI/CD en la rama de características.