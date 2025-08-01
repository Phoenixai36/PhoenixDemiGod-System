# Guía de Despliegue de Phoenix Hydra con Podman

## 1. Introducción

Esta guía proporciona instrucciones detalladas sobre cómo desplegar la pila de Phoenix Hydra utilizando Podman.

## 2. Instalación y Configuración de Podman

### 2.1. Instalación

```bash
# Para Fedora/CentOS/RHEL
sudo dnf install -y podman podman-docker podman-compose fuse-overlayfs slirp4netns
```

### 2.2. Configuración

```bash
systemctl --user enable --now podman.socket
mkdir -p ~/.config/containers/systemd
loginctl enable-linger $USER
```

### 2.3. Validación

```bash
podman info --format '{{.Host.Security.Rootless}}'
# Expected output: true
curl --unix-socket $XDG_RUNTIME_DIR/podman/podman.sock http://localhost/_ping
# Expected output: OK
```

## 3. Migración de Docker a Podman

Para migrar de Docker a Podman, siga estos pasos:

1.  Asegúrese de que Podman esté instalado y configurado correctamente.
2.  Elimine los contenedores y las imágenes de Docker.
3.  Despliegue la pila de Phoenix Hydra utilizando Podman.

## 4. Despliegue con Podman Compose

1.  Navegue al directorio `infra/podman`.
2.  Ejecute el comando `podman-compose up -d`.
3.  Verifique el estado de los servicios con `podman ps`.

## 5. Despliegue con Quadlet y systemd

1.  Copie los archivos `.container` y `.pod` de `infra/podman/systemd/` a `~/.config/containers/systemd/`.
2.  Ejecute el comando `systemctl --user daemon-reload`.
3.  Habilite e inicie el objetivo principal con `systemctl --user enable --now phoenix.target`.

## 6. Servicios de Observabilidad

La pila de Phoenix Hydra incluye los siguientes servicios de observabilidad:

*   Prometheus: Monitorización y alertas.
*   Grafana: Visualización de datos.
*   InfluxDB: Almacenamiento de series temporales.

Estos servicios se configuran en el archivo `infra/podman/observability.compose.yaml`.

## 7. Uso de Podman

Aquí hay algunos ejemplos de cómo utilizar Podman para gestionar los contenedores:

*   Listar los contenedores: `podman ps`
*   Detener un contenedor: `podman stop <container_id>`
*   Iniciar un contenedor: `podman start <container_id>`
*   Eliminar un contenedor: `podman rm <container_id>`

## 8. Conclusión

Esta guía proporciona instrucciones detalladas sobre cómo desplegar la pila de Phoenix Hydra utilizando Podman.