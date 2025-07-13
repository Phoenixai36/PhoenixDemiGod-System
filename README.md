AVISO DE CONFIDENCIALIDAD: Este documento es confidencial y propiedad de [Nombre de la Startup]. Su contenido es para uso exclusivo interno. Queda prohibida su distribución, copia o divulgación sin autorización expresa.

# Phoenix DemiGod System

> **Confidencial:** Este documento es confidencial y propiedad de [Nombre de la Startup]. Su distribución o reproducción no autorizada está prohibida.

Un sistema de IA avanzado para la orquestación autónoma de agentes especializados. Este proyecto integra múltiples tecnologías para lograr un sistema resiliente y capaz de auto-mejorarse.

## 🚀 Instalación

Siga estos pasos para configurar su entorno de desarrollo.

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd <NOMBRE_DEL_DIRECTORIO>
```

### 2. Entorno Virtual de Python

```bash
python -m venv venv
# En Windows:
.\venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate
```

### 3. Instalar Dependencias

```bash
# Dependencias de Python
pip install -r requirements.txt
# Dependencias de Node.js
npm install
```

## ⚙️ Configuración

La configuración principal se gestiona en el archivo [`config.yaml`](./config.yaml:1).

Para una guía detallada de todos los parámetros de configuración, consulta la [Documentación de Configuración](docs/configuracion.md).

Los secretos (tokens, claves de API, etc.) deben crearse localmente y **nunca** deben ser versionados. Cree los siguientes archivos en la raíz del proyecto:

* `.manager_token`
* `.worker_token`
* `.env`

Estos archivos son ignorados por Git a través de [`.gitignore`](./.gitignore:1).

## 🧪 Ejecución de Tests

Para ejecutar la suite completa de tests, use pytest:

```bash
pytest
```

## 📦 Despliegue

Para instrucciones detalladas sobre cómo desplegar y monitorizar el sistema, consulta la [Guía de Despliegue](docs/deployment-guide.md).

## 📂 Estructura del Repositorio

* **`BooPhoenix369/`**: Directorio principal que contiene la lógica del sistema, incluyendo agentes, scripts y configuraciones detalladas.
* **`src/`**: (Dentro de `BooPhoenix369`) Código fuente principal de la aplicación.
* **`tests/`**: Tests de integración y unitarios.
* **`scripts/`**: (Dentro de `BooPhoenix369`) Scripts para despliegue, mantenimiento y otras utilidades.
* **`config.yaml`**: Archivo de configuración principal del proyecto.

## 🛡️ Seguridad

**Importante:** Nunca suba archivos que contengan secretos, tokens o cualquier tipo de credencial al repositorio. Asegúrese de que archivos sensibles estén correctamente listados en el archivo [`.gitignore`](./.gitignore:1).

## CI/CD

Este proyecto utiliza un pipeline de Integración Continua para automatizar los tests. Para más detalles, consulta la [Documentación de CI/CD](docs/ci-cd.md).

## Calidad de Código y Colaboración

Para mantener un estándar de código consistente y facilitar la colaboración, utilizamos herramientas de formateo y linting automático.

### Pre-commit Hooks

Este proyecto usa `pre-commit` para verificar el código antes de que se realice un commit. Los hooks están configurados en el archivo [`.pre-commit-config.yaml`](./.pre-commit-config.yaml:1) y ejecutan `black` y `flake8` automáticamente.

Para empezar a usarlos, simplemente instálalos una vez:

```bash
pre-commit install
```

### Guía de Onboarding

Para una guía completa sobre cómo configurar tu entorno, instalar dependencias y empezar a contribuir, por favor consulta nuestra [Guía de Onboarding para Nuevos Desarrolladores](./docs/ONBOARDING.md:1).
