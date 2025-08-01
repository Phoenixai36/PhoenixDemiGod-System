# Guía Definitiva: Verificación de Despliegue del Stack "Phoenix DemiGod" en VS Code

Este documento establece el procedimiento estándar para verificar que el stack de aplicaciones "Phoenix DemiGod" se ha desplegado de manera exitosa y se encuentra completamente operativo. Está diseñado para que los desarrolladores puedan autodiagnosticar el estado del sistema de forma rápida y precisa.

---

## 1. Verificación de Servicios y Contenedores

El primer paso es confirmar que todos los microservicios, encapsulados como contenedores, están en ejecución y en buen estado.

Utilizamos `docker ps` o `podman ps` para listar los contenedores activos. El objetivo es verificar que cada componente del stack (`phoenix`, `ollama`, `n8n`, `windmill`, etc.) aparece en la lista y que su estado es `Up` o `running`.

```bash
# Comando para listar contenedores activos con Docker
docker ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"

# Comando equivalente para Podman
podman ps --format "table {{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}"
```

**Salida Esperada:**

```text
CONTAINER ID   NAMES               IMAGE                        STATUS
a1b2c3d4e5f6   phoenix-demigod-api phoenix-api:latest           Up 2 minutes
b2c3d4e5f6a1   ollama              ollama/ollama:latest         Up 2 minutes
c3d4e5f6a1b2   n8n                 n8nio/n8n:latest             Up 2 minutes
d4e5f6a1b2c3   windmill            windmill/windmill:latest     Up 2 minutes
```

Para un análisis de salud en tiempo real, `docker stats` o `podman stats` son herramientas invaluables. Permiten monitorear el consumo de CPU y memoria, lo cual es un excelente indicador de que los servicios no solo están "vivos", sino que están operando dentro de parámetros normales. Un consumo anómalo (0% o 100% de CPU constante) puede indicar un problema.

```bash
# Monitoreo de recursos en tiempo real
docker stats
```

### ### Problemas Comunes y Soluciones

* **Un contenedor no aparece en la lista:**
    1. Asegúrese de haber ejecutado `docker-compose up -d` o el script de inicio correspondiente.
    2. Si el comando se ejecutó, es probable que el contenedor haya fallado al iniciar. Use `docker ps -a` para ver *todos* los contenedores, incluidos los detenidos.
* **El estado del contenedor es `Exited` o `Restarting`:**
    1. Esto indica un error crítico durante el arranque o la ejecución. El paso inmediato es inspeccionar los logs del contenedor para identificar la causa raíz.
    2. Ejecute `docker logs <nombre_del_contenedor>` (ej. `docker logs phoenix-demigod-api`) para ver la salida de error. Busque mensajes como `Error: port is already allocated`, `database connection failed` o `ModuleNotFoundError`.

## 2. Pruebas Funcionales de Endpoints y APIs

Una vez confirmada la ejecución de los contenedores, el siguiente paso es validar la conectividad y la funcionalidad de las APIs y las interfaces web.

### ### Prueba de la API Principal con `curl`

La forma más directa de probar la API de `Phoenix` es enviando una petición `POST` a su endpoint de salud o a un endpoint funcional.

```bash
# Ejemplo de petición POST al endpoint /v1/chat/completions
curl -X POST http://localhost:8000/v1/chat/completions \
-H "Content-Type: application/json" \
-d '{
    "model": "llama3",
    "messages": [
        {
            "role": "user",
            "content": "Explica la importancia de los health checks en un sistema de microservicios."
        }
    ],
    "stream": false
}'
```

* `-X POST`: Especifica el método HTTP.
* `-H "Content-Type: application/json"`: Define el tipo de contenido que estamos enviando, crucial para que la API FastAPI lo interprete correctamente.
* `-d '{...}'`: Contiene el cuerpo (payload) de la petición en formato JSON.

Una **respuesta exitosa** será un objeto JSON con el código de estado `200 OK`, conteniendo la respuesta generada por el modelo, no un mensaje de error.

**Respuesta Exitosa de Ejemplo (JSON):**

```json
{
  "id": "chatcmpl-12345",
  "object": "chat.completion",
  "created": 1677652288,
  "model": "llama3",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Los health checks son fundamentales en microservicios porque..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 25,
    "completion_tokens": 50,
    "total_tokens": 75
  }
}
```

### ### Verificación de Interfaces Web

Acceda a las siguientes URLs en su navegador. Ver una página de inicio de sesión o un dashboard funcional confirma que el servicio está operativo.

| Servicio      | URL Local                 | Qué Esperar                                       |
|---------------|---------------------------|---------------------------------------------------|
| **Phoenix API**   | `http://localhost:8000/docs` | La interfaz interactiva de Swagger/OpenAPI.       |
| **Open WebUI**  | `http://localhost:8080`   | La interfaz de chat para interactuar con Ollama.  |
| **n8n**         | `http://localhost:5678`   | La página de configuración inicial o el dashboard de n8n. |
| **Windmill**    | `http://localhost:8082`   | La página de inicio de sesión o el dashboard de Windmill. |

### ### Problemas Comunes y Diagnóstico

* **`Connection Refused`**: El error más común. Significa que no hay ningún proceso escuchando en el puerto de destino.
  * **Causa probable:** El contenedor correspondiente no está corriendo (`docker ps`). Verifique la Sección 1.
  * **Causa secundaria:** El contenedor está corriendo, pero el mapeo de puertos en el `docker-compose.yml` es incorrecto o está en conflicto.
* **`404 Not Found`**: El servidor está activo, pero la ruta específica (`/v1/chat/completions`) no existe.
  * **Causa probable:** Error de tipeo en la URL o el endpoint ha cambiado. Verifique la documentación de la API (`/docs`).
* **`502 Bad Gateway`**: Típicamente visto cuando se usa un proxy inverso (como Nginx). Indica que el proxy está funcionando, pero no puede comunicarse con el servicio de backend (la API de Phoenix, por ejemplo).
  * **Causa probable:** El contenedor del backend (`phoenix-demigod-api`) se ha caído o está sobrecargado, mientras que el proxy sigue en pie. Revise los logs del contenedor de backend.

## 3. Validación Automatizada Integral con Scripts

El ecosistema "Phoenix DemiGod" incluye scripts de diagnóstico para automatizar la verificación completa del stack. Estos scripts son la forma más eficiente de obtener una confirmación de "sistema operativo".

* `.scripts/deploymentquicktest.sh`: Realiza una serie de pruebas rápidas, incluyendo pings a servicios, verificaciones de endpoints básicos y comprobaciones de configuración.
* `.PhoenixDemigodSystem.sh --test`: Ejecuta un conjunto de pruebas más exhaustivo, validando la integración entre los componentes, como la comunicación entre la API y Ollama.

Para ejecutar la validación, simplemente corra el script desde la terminal integrada de VS Code:

```bash
# Ejecutar el test rápido de despliegue
bash .scripts/deploymentquicktest.sh
```

Una **salida exitosa** será un informe claro y conciso, culminando con un mensaje de confirmación inequívoco.

**Salida Exitosa de Ejemplo:**

```text
[INFO] Iniciando test de despliegue de Phoenix DemiGod...
[OK] Contenedor 'phoenix-demigod-api' está operativo.
[OK] Contenedor 'ollama' está operativo.
[OK] Endpoint API /docs responde con 200 OK.
[OK] Conexión con el modelo 'llama3' en Ollama exitosa.
[SUCCESS] --------------------------------------------------
[SUCCESS]  SISTEMA PHOENIX DEMIGOD v8.7 COMPLETAMENTE OPERATIVO
[SUCCESS] --------------------------------------------------
```

### Nota de Mejores Prácticas

> **Ejecute siempre el script `deploymentquicktest.sh` después de cualquier `docker-compose up`, reinicio del sistema o actualización de una imagen.** Esto le proporcionará una confirmación inmediata del estado del sistema antes de comenzar a desarrollar o probar.

## 4. Integración y Monitoreo desde VS Code

El entorno de desarrollo está optimizado para gestionar y verificar el stack directamente desde Visual Studio Code, minimizando el cambio de contexto.

Use la **Paleta de Comandos** (`Ctrl+Shift+P` o `Cmd+Shift+P` en macOS) para acceder a las tareas predefinidas. Escriba "Tasks: Run Task" y seleccione una de las siguientes:

* **`Start Phoenix Complete Stack`**: Equivalente a `docker-compose up -d`, inicia todo el sistema en segundo plano.
* **`Test Model Router Integration`**: Ejecuta una prueba específica para validar que la API puede enrutar peticiones al modelo correcto en Ollama.
* **`Run Full System Check`**: Invoca el script de validación integral (`.PhoenixDemigodSystem.sh --test`).

El progreso y el resultado de estas tareas se mostrarán directamente en la **terminal integrada de VS Code**. Esto centraliza el flujo de trabajo: iniciar, probar y depurar, todo dentro del mismo editor.

Nota de Mejores Prácticas

> **Instale la extensión "Docker" de Microsoft en VS Code.** Proporciona una interfaz visual para:
>
> * Ver el estado de los contenedores (equivalente a `docker ps`).
> * Acceder a los logs de un contenedor con un solo clic.
> * Ejecutar comandos dentro de un contenedor (`exec`).
> * Reiniciar o detener servicios individuales.
>
> Esta extensión transforma la gestión de contenedores de una tarea de línea de comandos a una experiencia visual e intuitiva.

## 5. Análisis de Logs para Diagnóstico Avanzado

Cuando las pruebas automatizadas fallan o un contenedor se comporta de forma inesperada, el análisis de logs es el siguiente paso crítico.

Para visualizar los logs de todos los servicios en tiempo real y de forma agregada, use:

```bash
# Ver logs de todo el stack en tiempo real
docker-compose logs -f
```

Para aislar el problema, es más efectivo observar los logs de un contenedor específico:

```bash
# Ver logs en tiempo real del contenedor de la API
docker logs -f phoenix-demigod-api

# Ver logs en tiempo real del contenedor de Ollama
docker logs -f ollama
```

**Qué buscar en los logs para confirmar un inicio correcto:**

* **`phoenix-demigod-api`**: Busque la línea `Uvicorn running on http://0.0.0.0:8000`. Esto confirma que el servidor web de la API está listo para recibir peticiones.
* **`ollama`**: Busque mensajes que indiquen que está escuchando en su puerto y que los modelos se han cargado correctamente.
* **`windmill` / `n8n`**: Busque mensajes que indiquen "Application started successfully" o "Server listening on port...".

### ### Problemas Comunes y Mensajes de Error en Logs

* **`Error: listen EADDRINUSE: address already in use :::8000`**: El puerto 8000 ya está ocupado por otro proceso en su máquina. Detenga el proceso conflictivo o cambie el puerto en el archivo `docker-compose.yml`.
* **`psycopg2.OperationalError: connection to server at "db" (172.20.0.5), port 5432 failed`**: El servicio de API no puede conectarse a la base de datos. Asegúrese de que el contenedor de la base de datos (`db`) esté corriendo y sea accesible desde el contenedor de la API.
* **`Ollama: could not load model 'non_existent_model'`**: La API está intentando usar un modelo que no ha sido descargado o configurado en Ollama. Verifique la configuración del modelo.

## 6. Glosario Técnico: ¿Qué Significa "Deployado" en Phoenix DemiGod?

En el contexto del stack "Phoenix DemiGod", el término **"deployado"** no se refiere a un despliegue en producción en la nube, sino a un **estado de operatividad local completa**. Un sistema "deployado" es aquel donde:

1. **Todos los microservicios están activos:** Cada contenedor definido en `docker-compose.yml` está en estado `Up`.
2. **Los servicios están interconectados:** La API puede comunicarse con Ollama, la base de datos y otros servicios internos.
3. **Los endpoints son funcionalmente accesibles:** Las APIs responden correctamente a las peticiones y las interfaces web son navegables.
4. **El sistema ha pasado las validaciones automáticas:** Los scripts de prueba se ejecutan sin errores.

### ### Componentes Clave del Stack

* **Docker/Podman:** La plataforma de contenedorización que aísla y ejecuta cada microservicio. Es la base sobre la que se construye todo.
* **FastAPI (Phoenix API):** El cerebro de la aplicación. Un framework de Python que expone los endpoints de la API, gestiona la lógica de negocio y se comunica con otros servicios.
* **Ollama:** El motor de inferencia de modelos de lenguaje. Sirve los modelos de IA (como Llama 3) para que la API pueda consumirlos.
* **n8n / Windmill:** Plataformas de automatización y flujos de trabajo. Permiten orquestar tareas complejas que involucran a la API y otros sistemas.
* **Scripts de Validación:** Herramientas de diagnóstico que actúan como un "check-up" de salud automatizado para todo el sistema.
* **VS Code:** El entorno de desarrollo integrado (IDE) que centraliza el código, la gestión de contenedores, la ejecución de tareas y la depuración.

## 7. Resumen Ejecutivo para No Técnicos

Para confirmar que el sistema "Phoenix DemiGod" está funcionando correctamente, realizamos una serie de verificaciones que aseguran que todas sus partes están activas y comunicándose entre sí. Es un proceso de tres pasos: primero, confirmamos que todos los "empleados" (contenedores) han llegado a la oficina. Segundo, les hacemos una llamada rápida (probamos las APIs) para asegurarnos de que responden. Finalmente, ejecutamos un simulacro general (scripts automáticos) para ver si pueden trabajar juntos en una tarea. Si todo esto es exitoso, el sistema está "deployado" y listo para trabajar.

**Analogía del Equipo de Especialistas Digitales:**

Piense en el stack "Phoenix DemiGod" como un equipo de élite digital. **"Estar deployado" significa que todo el equipo está en sus puestos, comunicado y listo para la acción.**

* La **API de Phoenix (FastAPI)** es el *Director de Proyecto y Recepcionista*: recibe todas las solicitudes, entiende lo que se necesita y lo delega a la persona adecuada.
* **Ollama** es el *Cerebro Experto*: el especialista en inteligencia artificial que genera las respuestas y análisis complejos.
* **n8n y Windmill** son los *Asistentes de Automatización*: se encargan de las tareas repetitivas y de conectar a nuestro equipo con otras herramientas externas.
* **Docker** es la *Oficina Virtual*: proporciona a cada especialista su propio espacio de trabajo aislado para que no se molesten entre sí.
* Los **Scripts de Verificación** son el *Supervisor de Turno*: realiza una ronda rápida para asegurarse de que todos están presentes, despiertos y listos para recibir tareas.
