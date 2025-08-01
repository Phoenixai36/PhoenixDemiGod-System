# Phoenix Hydra - Documento de Dirección Consolidado

## 1. Visión General y Estrategia del Producto

El proyecto Phoenix Hydra tiene como objetivo desarrollar un sistema de inteligencia artificial avanzado, robusto y escalable. La estrategia del producto se centra en tres áreas clave:

*   **Infraestructura y Tecnología Core:** Construir una base sólida con un motor de revisión del sistema, una arquitectura de IA no basada en transformadores (Mamba/SSM) para un procesamiento 100% local y energéticamente eficiente, y un sistema de agentes biomiméticos (RUBIK) para un análisis adaptativo e inteligente.
*   **Monetización y Preparación para el Mercado:** Crear flujos de ingresos a través de programas de afiliados, asegurar financiación mediante subvenciones (NEOTEC, ENISA, EIC) e integrarse en los principales marketplaces (AWS, Cloudflare, Hugging Face).
*   **Automatización y Despliegue:** Garantizar la estabilidad y seguridad de los despliegues mediante un sistema de validación integral, automatizar la gestión de contenedores con Podman Compose y agilizar el desarrollo con pipelines de CI/CD y una profunda integración con VS Code.

El objetivo final es alcanzar el 100% de la finalización del sistema, asegurar las subvenciones clave, lanzarlo en los principales marketplaces e impulsar la adopción a través de programas de afiliados.

## 2. Arquitectura y Estructura del Sistema

La arquitectura de Phoenix Hydra se basa en tres pilares fundamentales:

*   **Arquitectura Orientada a Eventos:** El sistema se articula en torno a un robusto sistema de enrutamiento de eventos que desacopla los componentes y permite la comunicación asíncrona. Los componentes clave son el **Event Router**, el **Pattern Matcher**, el **Event Store** y el **Event Correlator**.
*   **Componentes Modulares y Componibles:** El sistema está formado por componentes independientes y reutilizables, cada uno con una responsabilidad específica. Esto incluye los **Agent Hooks**, el sistema de **Validación de Despliegues**, la **Automatización de Podman Compose** y el motor de **Revisión del Sistema Phoenix Hydra**.
*   **IA No Basada en Transformadores y Procesamiento Local:** Una iniciativa estratégica clave es la adopción de una arquitectura de IA no basada en transformadores, utilizando modelos Mamba/SSM para permitir capacidades 100% locales y offline.

La interacción entre componentes se produce principalmente a través del sistema de enrutamiento de eventos, lo que proporciona una arquitectura altamente escalable y resistente.

## 3. Refactorización de los Agent Hooks

La refactorización de los *agent hooks* es una iniciativa crucial para mejorar la modularidad, la capacidad de prueba y la mantenibilidad del sistema. Los objetivos clave son:

*   **Refactorización Arquitectónica:** Migrar todos los *hooks* existentes a una nueva arquitectura unificada.
*   **Modularidad Mejorada:** Desacoplar los *hooks* individuales del sistema central.
*   **Capacidad de Prueba Mejorada:** Implementar pruebas unitarias y de integración exhaustivas para cada *hook*.
*   **Configuración Dinámica:** Introducir un registro y un sistema de configuración centralizados para la gestión dinámica de los *hooks*.
*   **Patrones de Desarrollo Claros:** Proporcionar documentación y ejemplos claros para agilizar el desarrollo de nuevos *hooks*.

## 4. Planes de Implementación Detallados

A continuación se presenta un resumen de los planes de implementación para cada uno de los principales componentes del sistema:

### 4.1. Enrutamiento de Eventos

*   **Estado:** Las interfaces principales y los modelos de datos ya están implementados.
*   **Tareas Pendientes:** Migrar la implementación existente a una estructura de módulos adecuada, implementar el almacén de eventos, el correlador de eventos, el reproductor de eventos y la integración de los *agent hooks*. Se requiere una amplia cobertura de pruebas unitarias y de integración.

### 4.2. Validación de Despliegues

*   **Estado:** Plan de implementación definido.
*   **Tareas Pendientes:** Configurar la estructura del proyecto, implementar el servicio de contenedores para las operaciones de Podman, construir el sistema de validación de salud, el marco de pruebas funcionales, el orquestador del gestor de despliegues, el sistema de validación de seguridad, el sistema de informes, la interfaz de línea de comandos y la integración con las tareas de VS Code.

### 4.3. Refactorización de los Agent Hooks

*   **Estado:** Infraestructura central completada. Migración del *Cellular Communication Hook* en curso.
*   **Tareas Pendientes:** Completar la migración de todos los *hooks* (Container Health Restart, Container Log Analysis, Container Resource Scaling, Example), mejorar la integración del enrutador de eventos, implementar el registro de *hooks* y el sistema de configuración, y crear un conjunto de pruebas de integración exhaustivo.

### 4.4. Revisión del Sistema Phoenix Hydra

*   **Estado:** La mayoría de los componentes del motor de descubrimiento, análisis, evaluación y generación de informes están implementados.
*   **Tareas Pendientes:** Implementar la lógica no basada en transformadores y la arquitectura de procesamiento local, incluyendo la integración de la arquitectura del modelo Mamba/SSM, la infraestructura de procesamiento local, el sistema de agentes biomiméticos RUBIK y los motores de análisis no basados en transformadores.

### 4.5. Automatización de Podman Compose

*   **Estado:** Plan de implementación definido.
*   **Tareas Pendientes:** Configurar los modelos de datos y las estructuras de configuración, implementar el gestor de entorno, construir el gestor de composición para la orquestación central, crear el monitor de salud, desarrollar la integración de eventos, construir la integración con VS Code, implementar un manejo de errores exhaustivo y añadir capacidades de registro y monitorización.