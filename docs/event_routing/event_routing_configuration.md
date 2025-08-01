# Configuración del Sistema de Enrutamiento de Eventos

## 1. Introducción

Este documento proporciona información detallada sobre la configuración y el despliegue del sistema de enrutamiento de eventos.

## 2. Parámetros de Configuración

Los siguientes parámetros de configuración están disponibles:

*   `event_store_type`: El tipo de Event Store a utilizar (por ejemplo, `memory`, `mongodb`, `influxdb`).
*   `event_store_uri`: La URI del Event Store.
*   `event_correlator_enabled`: Indica si el Event Correlator está habilitado o no.
*   `event_replayer_enabled`: Indica si el Event Replayer está habilitado o no.

## 3. Ejemplos de Configuración

### 3.1. Desarrollo

```yaml
event_store_type: memory
event_store_uri: ""
event_correlator_enabled: true
event_replayer_enabled: true
```

### 3.2. Pruebas

```yaml
event_store_type: mongodb
event_store_uri: "mongodb://localhost:27017/event_store_test"
event_correlator_enabled: true
event_replayer_enabled: true
```

### 3.3. Producción

```yaml
event_store_type: influxdb
event_store_uri: "http://localhost:8086"
event_correlator_enabled: true
event_replayer_enabled: true
```

## 4. Despliegue

Para desplegar el sistema de enrutamiento de eventos en un entorno de producción, siga estos pasos:

1.  Configure el Event Store.
2.  Configure el Event Correlator (opcional).
3.  Configure el Event Replayer (opcional).
4.  Despliegue los componentes del sistema de enrutamiento de eventos.

## 5. Conclusión

Este documento proporciona información detallada sobre la configuración y el despliegue del sistema de enrutamiento de eventos.