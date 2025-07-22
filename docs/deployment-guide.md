<!-- # Guía de Despliegue -->

Esta guía proporciona instrucciones detalladas sobre cómo desplegar y monitorizar la aplicación Phoenix DemiGod utilizando los scripts proporcionados.

## Despliegue del Stack

El script `deploy-stack.sh` se encarga de desplegar la pila completa de la aplicación en un clúster de Docker Swarm.

### Uso

Para ejecutar el script, navega al directorio `BooPhoenix369/scripts/` y ejecuta el siguiente comando:

```bash
./deploy-stack.sh [entorno]
```

### Argumentos

* `[entorno]` (opcional): Especifica el entorno de despliegue. Los valores posibles son:
  * `production` (por defecto)
  * `staging`
  * `development`

Si no se proporciona ningún entorno, el script utilizará `production` por defecto.

### Proceso

1. **Comprobación de Docker Swarm**: Verifica si Docker Swarm está activo. Si no lo está, el script se detendrá.
2. **Carga de variables de entorno**: Carga las variables desde un archivo `.env` si existe en el directorio raíz del proyecto.
3. **Selección del archivo de Compose**: Elige el archivo `docker-compose` correspondiente al entorno especificado.
4. **Despliegue del Stack**: Utiliza `docker stack deploy` para desplegar la pila con el nombre `phoenix`.
5. **Verificación de Servicios**: Después del despliegue, comprueba el estado de los servicios para asegurar que se han iniciado correctamente.

## Monitorización del Stack

El script `monitor-stack.sh` proporciona herramientas para observar el estado y los logs de la pila desplegada.

### Uso del script de monitorización

Para utilizar el script de monitorización, navega al directorio `BooPhoenix369/scripts/` y ejecuta el comando con una de las siguientes opciones:

```bash
./monitor-stack.sh [opción]
```

### Opciones

* `-s` o `--services`: Muestra una lista de todos los servicios que se están ejecutando en el stack `phoenix`.
* `-l SERVICE_NAME` o `--logs SERVICE_NAME`: Muestra los logs del servicio especificado. Reemplaza `SERVICE_NAME` con el nombre del servicio que deseas inspeccionar (por ejemplo, `api`).
* `-f` o `--follow` (usado con `-l`): Sigue la salida de los logs en tiempo real.
* `-h` o `--help`: Muestra un mensaje de ayuda con las opciones disponibles.

Si se ejecuta sin argumentos, el script mostrará una vista general del estado del stack que se actualiza cada 10 segundos.

## 🔒 Gestión de Secretos en Producción

**Importante:** Para entornos de `staging` y `production`, el uso de archivos `.env` está **estrictamente desaconsejado** por razones de seguridad.

En su lugar, la configuración y los secretos deben ser gestionados a través de una herramienta centralizada y segura, como:

*   **HashiCorp Vault**
*   **AWS Secrets Manager**
*   **Azure Key Vault**
*   **Docker Secrets** (para entornos Swarm)

Estas herramientas proporcionan cifrado, control de acceso granular y auditoría, que son fundamentales para proteger la información sensible en un entorno de producción. El pipeline de despliegue debe estar configurado para inyectar estos secretos de forma segura durante el arranque de los contenedores, sin exponerlos en el código fuente ni en los logs.

### Ejemplos

**Mostrar todos los servicios:**

```bash
./monitor-stack.sh -s
```

**Mostrar los logs del servicio `api`:**

```bash
./monitor-stack.sh -l api
```

**Seguir los logs del servicio `api` en tiempo real:**

```bash
./monitor-stack.sh -l api -f
```