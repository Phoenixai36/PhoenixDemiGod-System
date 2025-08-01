# 3. Guía de Despliegue

Esta guía detalla los pasos necesarios para desplegar el sistema Phoenix DemiGod en un entorno de desarrollo local utilizando Podman.

## 3.1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalados y configurados los siguientes requisitos en tu sistema:

-   **Podman:** Como motor de contenedores principal. Asegúrate de que el servicio de Podman esté iniciado y funcionando correctamente.
-   **Python 3.13+:** Necesario para la ejecución de diversos scripts de soporte y utilidades del proyecto.
-   **WSL2 (Windows Subsystem for Linux):** Requerido si estás desplegando en un sistema Windows para garantizar la compatibilidad y el rendimiento de los contenedores.

## 3.2. Pasos de Despliegue

Sigue estos pasos en orden para realizar un despliegue exitoso.

### Paso 1: Clonar el Repositorio

Para comenzar, clona el repositorio del proyecto desde su origen a tu máquina local y navega al directorio del proyecto.

```bash
# Reemplaza la URL con la del repositorio correspondiente
git clone https://github.com/tu-usuario/phoenix-demigod.git
cd phoenix-demigod
```

### Paso 2: Configurar el Entorno

El proyecto utiliza un archivo `.env` para gestionar las variables de entorno, que incluyen secretos y configuraciones específicas de la instancia.

1.  **Crear el archivo de configuración:**
    Copia el archivo de ejemplo [`.env.example`](.env.example) a un nuevo archivo llamado `.env`. Este comando funciona tanto en PowerShell como en terminales bash.

    ```bash
    cp .env.example .env
    ```

2.  **Rellenar las variables:**
    Abre el archivo `.env` con un editor de texto y completa todas las variables requeridas (API keys, contraseñas, etc.).

> **Importante:** El archivo `.env` contiene información sensible y **nunca** debe ser añadido al control de versiones (Git). El archivo [`.gitignore`](.gitignore) del proyecto ya está configurado para ignorarlo y prevenir commits accidentales.

### Paso 3: Ejecutar el Script de Despliegue

El script [`phoenix-deploy-complete.ps1`](phoenix-deploy-complete.ps1) automatiza todo el proceso de despliegue. Se encarga de construir las imágenes de los contenedores, configurar las redes y volúmenes necesarios, y levantar toda la pila de servicios con Podman.

Ejecuta el siguiente comando desde una terminal de **PowerShell**:

```powershell
./phoenix-deploy-complete.ps1
```

## 3.3. Verificación del Despliegue

Una vez que el script haya finalizado sin errores, puedes verificar que todos los servicios se están ejecutando correctamente.

1.  **Listar contenedores activos:**
    Usa el siguiente comando para ver todos los contenedores que están en ejecución.

    ```bash
    podman ps
    ```

    Deberías ver una lista de contenedores con el estado `Up` o `Running`.

2.  **Revisar logs de un contenedor:**
    Si algún contenedor no se inicia o quieres verificar su salida, puedes inspeccionar sus logs.

    ```bash
    # Reemplaza <nombre_o_id_del_contenedor> con el valor real
    podman logs <nombre_o_id_del_contenedor>
    ```

## 3.4. Solución de Problemas Comunes (Troubleshooting)

Aquí se listan algunos de los problemas más comunes y sus posibles soluciones.

#### El script `phoenix-deploy-complete.ps1` falla al ejecutarse

-   **Causa:** La política de ejecución de PowerShell en tu sistema puede estar restringiendo la ejecución de scripts locales.
-   **Solución:** Abre una terminal de PowerShell como Administrador y ejecuta el siguiente comando para permitir la ejecución de scripts para la sesión actual:
    ```powershell
    Set-ExecutionPolicy RemoteSigned -Scope Process
    ```

#### Problemas de conexión con Podman

-   **Causa:** El servicio o la máquina virtual de Podman no está en ejecución.
-   **Solución:** Asegúrate de que la máquina de Podman esté iniciada.
    ```bash
    podman machine start
    ```

#### Un contenedor no se inicia o se reinicia en bucle

-   **Causa:** Generalmente, esto se debe a una configuración incorrecta en el archivo `.env` (ej. una API key incorrecta o un formato de variable inválido).
-   **Solución:** Revisa cuidadosamente los logs del contenedor afectado con `podman logs <nombre_del_contenedor>` para identificar el error específico. Luego, corrige el valor correspondiente en tu archivo `.env` y reinicia el despliegue.