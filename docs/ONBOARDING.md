AVISO DE CONFIDENCIALIDAD: Este documento es confidencial y propiedad de [Nombre de la Startup]. Su contenido es para uso exclusivo interno. Queda prohibida su distribución, copia o divulgación sin autorización expresa.

# Guía de Onboarding para Nuevos Desarrolladores

> **Confidencial:** Este documento es confidencial y propiedad de [Nombre de la Startup]. Su distribución o reproducción no autorizada está prohibida.

¡Bienvenido/a al proyecto! Esta guía te ayudará a configurar tu entorno de desarrollo y a empezar a contribuir.

## Primeros Pasos

Sigue estos pasos para tener el proyecto funcionando en tu máquina local.

### 1. Requisitos Previos

Asegúrate de tener instalado lo siguiente:

* Python 3.8+
* pip (gestor de paquetes de Python)
* Git

### 2. Instalación

1. **Clona el repositorio:**

    ```bash
    git clone <URL-DEL-REPOSITORIO>
    cd <NOMBRE-DEL-DIRECTORIO>
    ```

2. **Crea y activa un entorno virtual:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
    ```

3. **Instala las dependencias:**

    ```bash
    pip install -r requirements.txt
    ```

### 3. Configuración de Pre-commit

Este proyecto utiliza `pre-commit` para asegurar que el código cumple con los estándares de calidad antes de ser enviado. Instala los hooks con el siguiente comando:

```bash
pre-commit install
```

Ahora, `black` y `flake8` se ejecutarán automáticamente en los archivos modificados antes de cada commit.

### 4. Ejecución de Tests

Para asegurarte de que todo funciona correctamente, ejecuta la suite de tests:

```bash
pytest
```

## Reporte de Bugs y Solicitud de Ayuda

* **Reportar un Bug:** Si encuentras un error, por favor, abre un "Issue" en nuestro repositorio de GitHub. Incluye una descripción detallada, los pasos para reproducirlo y cualquier log relevante.
* **Pedir Ayuda:** Si tienes dudas o necesitas ayuda, no dudes en contactar al equipo a través de nuestro canal de Slack o abriendo un "Issue" con tu pregunta.
