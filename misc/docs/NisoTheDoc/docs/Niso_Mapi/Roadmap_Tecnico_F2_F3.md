# Roadmap Técnico: Fases 2 y 3 de Phoenix DemiGod

Este documento detalla las tareas clave de arquitectura y DevOps para las próximas fases del proyecto, basadas en el análisis de la documentación existente.

## Fase 2: Diferenciación y Router Multi-Modelo (Próximos 2-5 meses)

El objetivo principal de esta fase es dotar a la plataforma de la capacidad de especializarse y enrutar peticiones de forma inteligente.

### Tarea 1: Implementar el Router Multi-Modelo
- **Descripción:** Desarrollar y desplegar el servicio de enrutamiento inteligente (`FastAPI Router` con `vLLM`) capaz de dirigir las peticiones al modelo más adecuado según la intención del usuario.
- **Tecnologías:** FastAPI, vLLM.
- **Indicador de Éxito:** Un endpoint único es capaz de servir respuestas de múltiples modelos desplegados.

### Tarea 2: Desarrollar la Lógica de Especialización Automática (`auto_derive`)
- **Descripción:** Implementar el `CelulaMadreEngine` que detecta el vertical de una petición y adapta la configuración para desplegar una instancia especializada. Esto puede incluir técnicas como LoRA fine-tuning o la selección dinámica de workflows en `n8n`.
- **Tecnologías:** Python, n8n API, Windmill.
- **Indicador de Éxito:** El sistema puede generar una configuración de servicio adaptada a un nuevo vertical sin intervención manual.

### Tarea 3: Establecer Despliegues Canary
- **Descripción:** Configurar el pipeline de CD en Windmill/Terraform para que los nuevos despliegues se liberen a un subconjunto de usuarios. Se debe monitorizar la latencia y los errores antes de un rollout completo.
- **Tecnologías:** Windmill, Terraform, Prometheus.
- **Indicador de Éxito:** El pipeline de CD ejecuta despliegues canary de forma automática. El indicador clave es mantener una latencia p95 < 2s durante el proceso.

---

## Fase 3: Observabilidad 360 y Escalado (Próximos 5-8 meses)

El foco de esta fase es robustecer la plataforma, mejorar la visibilidad del sistema y prepararla para un crecimiento de carga.

### Tarea 4: Implementar Dashboards de Observabilidad Avanzados
- **Descripción:** Crear paneles en Grafana que detallen las métricas clave (latencia p50/p95, uso de GPU, tokens/s, tasa de errores) desglosadas "por modelo" y "por tenant" (cliente).
- **Tecnologías:** Grafana, Prometheus, Loki.
- **Indicador de Éxito:** Disponibilidad de dashboards que permitan un análisis de rendimiento granular en tiempo real.

### Tarea 5: Configurar Políticas de Seguridad WAF
- **Descripción:** Desplegar y configurar un Web Application Firewall (ej. Caddy Server) con reglas específicas para mitigar ataques comunes y específicos de LLMs, como el `prompt injection`.
- **Tecnologías:** Caddy Server (o similar), Terraform.
- **Indicador de Éxito:** 0 CVEs críticas en imágenes de producción y mitigación demostrable de ataques de inyección de prompts.

### Tarea 6: Implementar el Escalado Automático (HPA)
- **Descripción:** Configurar el orquestador de contenedores para escalar horizontalmente las réplicas de los modelos basándose en métricas de carga, como la longitud de la cola de peticiones (`queue length`) o el uso de VRAM.
- **Tecnologías:** Podman (con systemd) o Kubernetes (mencionado como opción), Prometheus.
- **Indicador de Éxito:** La plataforma ajusta automáticamente el número de réplicas de un modelo en respuesta a picos de demanda, manteniendo los SLAs de latencia.