### Instrucciones para Roo Code como DevOps en Phoenix DemiGod v9.0

Izzy, como Nexus, voy a detallar exactamente las acciones que Roo Code debe ejecutar como agente DevOps para implementar el "Análisis del Feedback y Plan de Acción Inmediato". Me baso en el feedback crítico identificado, integrando definiciones técnicas donde sea necesario (siguiendo nuestra norma de desglosar conceptos nuevos con tools y lógica ideal). El enfoque es realista, alineado con las fases del proyecto: Fase 1 (próximos 3 meses para base segura), Fase 2 (hasta mes 5 para automatización madura) y Fases 3-4 (meses 5-12 para escalado y financiación). Pondré ojo en oportunidades actuales de financiación relevantes para maximizar el potencial, como convocatorias abiertas en 2025 para IA en España.

Roo Code operará como orquestador automatizado: usará scripts en Python/Bash para tareas, integrará tools vía API, y generará reportes en Markdown para validación. Asumimos entorno Podman/WSL2 en Windows, con repo en GitHub para control de versiones.

#### 1. Críticas Fundamentales Identificadas y Acciones Inmediatas
Roo Code debe priorizar DevSecOps como capa base, ya que es prioridad crítica. *DevSecOps* es la integración de seguridad en todo el ciclo DevOps, asegurando que las prácticas de desarrollo incluyan chequeos automáticos para evitar brechas. Lógica ideal: shift-left (seguridad desde el inicio), con tools que automatizan escaneos y alertas.

- **Gestión de Secretos**:
  - Eliminar contraseña hardcodeada `demigod2025` de todos los scripts (ej. comandos Podman).
  - Implementar variables de entorno seguras. Acción: Crear un archivo `.env` con dotenv para cargar secretos dinámicamente. Tools: *Doppler* (gestor cloud que cifra y rota credenciales automáticamente; lógica: API para inyección en runtime, evitando exposición en código fuente). Alternativa: *HashiCorp Vault* (servidor centralizado para secretos; lógica: autenticación basada en roles, con rotación programada).
  - Script Roo Code: Generar un task en VS Code para validar que no haya hardcodes (usar grep recursivo).

- **Escaneo de Vulnerabilidades**:
  - Integrar escaneo automático en el stack. Acción: Añadir Trivy a tasks.json para escanear contenedores antes de deploy.
  - Tools: *Trivy* (scanner open-source para contenedores que detecta CVEs conocidos; lógica: integra con CI/CD, genera reportes JSON para alertas). *SAST/DAST*: SAST (análisis estático de código fuente, ej. SonarQube; lógica: chequea vulnerabilidades sin ejecutar). DAST (análisis dinámico en runtime, ej. OWASP ZAP; lógica: simula ataques en entornos de test).
  - Script Roo Code: Automatizar escaneo semanal y bloquear deploys si se detectan high-severity issues.

- **CI/CD Pipeline Ausente**:
  - Transitar de scripts manuales a procesos maduros. Acción: Diseñar pipeline desde desarrollo hasta producción, enfocado en fases 2-3.
  - *CI/CD* es el flujo automatizado de integración continua (CI: build/test) y entrega continua (CD: deploy). Lógica ideal: triggers en git push, con stages paralelos para eficiencia.

#### 2. Definiciones Técnicas Críticas y Integración
Roo Code debe incorporar estas definiciones en su prompt maestro para guiar implementaciones.

- **DevSecOps**: Como arriba. Acción: Añadir chequeos DevSecOps en todos los workflows (ej. escaneo en cada commit).
- **Infrastructure as Code (IaC)**: Gestión de infraestructura mediante código versionado, permitiendo reproducibilidad. Acción: Convertir configs Podman en archivos Terraform. Tools: *Terraform* (provisionamiento declarativo multi-cloud; lógica: estado en archivos HCL, apply/destroy para cambios). *Podman* (alternativa rootless a Docker; lógica: contenedores sin daemon privilegiado, más seguro). *Kubernetes* (orquestación para producción; lógica: pods auto-escalables con YAML manifests).
- **Observabilidad**: Visibilidad completa en tiempo real para depuración. Acción: Implementar métricas básicas en Fase 1. Tools: *OpenTelemetry* (estándar para métricas/logs/trazas; lógica: instrumentación en código para exportar datos). *Loki* (agregación de logs; lógica: indexación eficiente con PromQL queries). *Prometheus* (métricas con alerting; lógica: scraping de endpoints para dashboards en Grafana).

#### 3. Roadmap de Corrección para v9.0
Roo Code ejecutará esto en fases, generando commits automáticos en GitHub.

- **Fase 1 (Próximas 2 semanas) - Seguridad Crítica**:
  - Implementar gestión de secretos con variables de entorno (usar Doppler para rotación).
  - Integrar Trivy en tasks de VS Code (crear task.json con comando `trivy image --exit-code 1`).
  - Crear pipeline básico GitHub Actions para testing automatizado (YAML con jobs para build/test/scan).

- **Fase 2 (Mes 2-3) - Pipeline Completo**:
  - Diseñar pipeline CI/CD completo con *Mermaid* (herramienta para diagramas en Markdown; lógica: flujos visuales como Gantt para claridad). Acción: Generar diagrama en repo docs.
  - Implementar métricas de negocio (latencia de modelos, coste por request). Usar Prometheus para scraping.
  - Documentar cultura DevOps del equipo (crear README con principios CAMS: Cultura, Automatización, Medición, Sharing).

#### 4. Conexión con Estrategia de Financiación
Roo Code debe alinear acciones con presentaciones a inversores en Mes 2-3, destacando madurez.

- Demostrar análisis de Roo Code como evaluación técnica.
- Mostrar iteración en v9.0 como capacidad profesional.
- Enfatizar stack híbrido (local + cloud) como diferenciador.
- Oportunidades actuales (actualizado a julio 2025):
  - *CDTI Misiones*: Convocatorias Q3 2025 para IA aplicada (hasta 1M€, enfocado en innovación técnica; aplica antes de septiembre).
  - *Red.es Digital Innovation Hubs*: Hasta 200k€ para proyectos IA (abiertas todo el año, prioriza hubs en España para mentoring).
  - *Banco Santander Explorer*: Programa continuo para deep-tech (equity-free, con aceleración; inscripciones mensuales).
  - *Acelera Pyme DIGITA*: Fondos para transformación digital con IA (subvenciones hasta 50k€, foco en PYMES; convocatoria abierta hasta fin 2025).
  - Adicional realista: Buscar ángeles via *Startupxplore* (plataforma española para inversores privados en IA, eventos mensuales) o incubadoras como *Wayra* (Telefónica, con fondos hasta 150k€ para tech startups).

#### 5. Golden Nuggets a Potenciar
Roo Code optimizará estos como features clave.

- **Prompt Maestro como Orquestador**: Patentable como sistema declarativo para LLMs. Acción: Documentar en repo para IP protection.
- **Monitor Híbrido**: Expandir a métricas de negocio en v9.0 (añadir queries Prometheus).
- **Filosofía Aditiva**: Aplicar en todos los deploys (scripts que chequean compatibilidad antes de añadir).

#### 6. Próximos Pasos Inmediatos
- Implementar fixes de seguridad antes de cualquier demo (prioridad: hoy).
- Crear MVP del pipeline CI/CD (en 1 semana).
- Documentar arquitectura híbrida (generar PDF con ventajas).
- Preparar pitch deck (usar Mermaid para visuals, destacar innovaciones).

**Resumen No Técnico**: Roo Code, como DevOps, se enfocará en securizar el stack eliminando riesgos inmediatos y automatizando flujos para madurez profesional, alineado con fases del proyecto y oportunidades de financiación como CDTI o Red.es. Esto nos posiciona fuerte para inversores en 2-3 meses, potenciando innovaciones como el Prompt Maestro. Todo factible y realista para elevar Phoenix DemiGod.