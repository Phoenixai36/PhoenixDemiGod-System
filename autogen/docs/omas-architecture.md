# Arquitectura de OMAS

## Propósito
OMAS (Open Multi-Agent System) es el framework que gestiona la coordinación y comunicación entre agentes en Phoenix DemiGod.

## Componentes Principales
- **Agentes**: Definidos en `omas/agents/`.
- **Reglas**: Especificadas en `omas/rules/`.
- **Configuraciones**: Globales en `omas/configs/`.

## Diagrama de Arquitectura
```mermaid
graph TD
    A[OMAS] --> B[Agentes]
    B --> C[Reglas]
    B --> D[Logs]
    A --> E[Configuraciones]