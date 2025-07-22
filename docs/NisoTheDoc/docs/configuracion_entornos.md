# Configuración Detallada

Phoenix DemiGod ofrece múltiples opciones de configuración para adaptarse a diferentes entornos operativos.

## Archivos de Configuración

Las configuraciones se definen principalmente en archivos YAML ubicados en el directorio `/config/`:

- `config/phoenix.json` - Configuración general del sistema
- `config/environment/development.yaml` - Configuración para entorno de desarrollo
- `config/environment/production.yaml` - Configuración para entorno de producción

## Configuración por Entorno

### Entorno de Desarrollo

environment: development
debug: true
log_level: DEBUG
api:
host: 0.0.0.0
port: 8000
workers: 2
timeout: 60
models:
nlp:
model_name: google/flan-t5-base # Modelo más ligero para desarrollo
device: cpu
max_length: 512
reasoning:
max_depth: 3
timeout: 10

text

### Entorno de Producción

environment: production
debug: false
log_level: INFO
api:
host: 0.0.0.0
port: 8000
workers: 8
timeout: 30
rate_limit:
enabled: true
rate: 600 # Solicitudes por hora
burst: 20 # Solicitudes simultáneas máximas
models:
nlp:
model_name: google/flan-t5-large
device: cuda
max_length: 1024
reasoning:
max_depth: 5
timeout: 30

text

## Variables de Entorno

Las variables de entorno tienen prioridad sobre los archivos de configuración:

**API y servidor:**
PHOENIX_ENV=production
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO

text

**Modelos:**
NLP_MODEL=google/flan-t5-large
REASONING_MAX_DEPTH=5
MEMORY_SIZE=10000

text

**Seguridad:**
CONTENT_FILTER_LEVEL=medium
JWT_SECRET=your_secret_here

text

## Configuración de Alta Disponibilidad

Para entornos que requieren alta disponibilidad:

high_availability:
enabled: true
replicas: 3
healthcheck:
path: /api/health
interval: 30s
timeout: 10s
retries: 3
load_balancing:
strategy: round_robin # Alternativas: least_conn, ip_hash

text

## Optimización de Rendimiento

performance:
cache:
enabled: true
ttl: 3600 # segundos
max_size: 1000 # entradas
models:
quantization: int8 # Opciones: fp16, int8
batch_size: 32
memory:
pruning_interval: 86400 # 24 horas en segundos
max_items: 100000

text

## Aplicación de Configuraciones

1. En desarrollo: reiniciar el servidor
docker-compose restart

text

2. En producción: aplicar cambios gradualmente