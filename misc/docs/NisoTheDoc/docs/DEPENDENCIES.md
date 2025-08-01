# Dependencias del Proyecto

Este archivo documenta las dependencias del proyecto Phoenix DemiGod identificadas hasta el momento.

## Dependencias Clave

- **Docker:** El proyecto utiliza Docker para la contenerización y el despliegue. Sin embargo, la configuración actual de Docker presenta problemas y necesita ser resuelta.
- **Traefik:** Se utiliza Traefik como proxy inverso y balanceador de carga. La configuración se encuentra en `config/traefik-config.toml`.
- **Scripts de Shell:** Varios scripts de shell en el directorio `scripts/` gestionan el despliegue y la configuración del entorno.

## Próximos Pasos

- **Investigar los archivos `docker-compose.yml`:** Estos archivos son esenciales para definir las dependencias de las imágenes de Docker y los servicios. Una vez que se localicen, se deben analizar para documentar completamente las dependencias del proyecto.