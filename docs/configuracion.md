# Documentación de Configuración (`config.yaml`)

Este documento detalla la estructura y los parámetros del archivo de configuración principal `config.yaml`.

## Estructura General

El archivo está organizado en secciones principales para agrupar configuraciones relacionadas:

- `database`: Contiene todos los parámetros para la conexión con la base de datos.
- `api_keys`: Almacena las claves de API necesarias para interactuar con servicios de terceros.
- `logging`: Define el comportamiento del sistema de registro de eventos (logs).

---

### Sección `database`

Parámetros para establecer la conexión con la base de datos.

- **`host`**:
  - **Descripción:** La dirección del servidor de la base de datos.
  - **Valores esperados:** Una cadena de texto (string), como una dirección IP o un nombre de dominio.
  - **Por defecto:** `"localhost"`

- **`port`**:
  - **Descripción:** El puerto en el que la base de datos está escuchando.
  - **Valores esperados:** Un número entero (integer).
  - **Por defecto:** `5432`

- **`user`**:
  - **Descripción:** El nombre de usuario para autenticarse en la base de datos.
  - **Valores esperados:** Una cadena de texto (string).
  - **Por defecto:** `"admin"`

- **`password`**:
  - **Descripción:** La contraseña para el usuario especificado.
  - **Valores esperados:** Una cadena de texto (string).
  - **Por defecto:** `"password_seguro"`

- **`dbname`**:
  - **Descripción:** El nombre de la base de datos a la que conectarse.
  - **Valores esperados:** Una cadena de texto (string).
  - **Por defecto:** `"mi_aplicacion"`

---

### Sección `api_keys`

Esta sección se utiliza para gestionar las credenciales de servicios externos.

- **`servicio_externo_1`**:
  - **Descripción:** Clave de API para el "Servicio Externo 1".
  - **Valores esperados:** Una cadena de texto (string).
  - **Por defecto:** `"clave_secreta_123"`

- **`servicio_externo_2`**:
  - **Descripción:** Clave de API para el "Servicio Externo 2".
  - **Valores esperados:** Una cadena de texto (string).
  - **Por defecto:** `"otra_clave_secreta_456"`

---

### Sección `logging`

Configura cómo se registran los eventos y errores de la aplicación.

- **`level`**:
  - **Descripción:** El nivel mínimo de severidad para que un mensaje sea registrado.
  - **Valores esperados:** `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`.
  - **Por defecto:** `"INFO"`

- **`file`**:
  - **Descripción:** El nombre del archivo donde se guardarán los logs.
  - **Valores esperados:** Una cadena de texto (string) con una ruta de archivo válida.
  - **Por defecto:** `"app.log"`

- **`max_size_mb`**:
  - **Descripción:** El tamaño máximo del archivo de log en megabytes antes de rotar.
  - **Valores esperados:** Un número entero (integer).
  - **Por defecto:** `10`

- **`backup_count`**:
  - **Descripción:** El número de archivos de log antiguos que se conservarán.
  - **Valores esperados:** Un número entero (integer).
  - **Por defecto:** `5`
