# System Structure Steering Document

## Overview

This document provides a high-level overview of the system structure for the Phoenix Hydra project. It outlines the core components, their responsibilities, and the relationships between them. The goal is to establish a clear and scalable architecture that supports the project's long-term objectives.

## Core Architectural Pillars

### 1. Event-Driven Architecture

The entire system is built upon a robust event-driven architecture. The **Event Routing** system is the central nervous system, responsible for decoupling components and enabling asynchronous communication.

*   **Event Router:** The central message bus for publishing and subscribing to events.
*   **Pattern Matcher:** A sophisticated component for matching events against subscription patterns, including wildcards and attribute filters.
*   **Event Store:** A persistent store for all events, enabling replay and historical analysis.
*   **Event Correlator:** A component for tracking and managing event correlation chains, providing a complete audit trail for complex workflows.

### 2. Modular and Composable Components

The system is composed of a set of modular and composable components, each with a specific responsibility. This approach promotes separation of concerns, reusability, and independent development.

*   **Agent Hooks:** A collection of independent agents that subscribe to events and perform specific actions, such as container health checks, log analysis, and resource scaling.
*   **Deployment Validation:** A comprehensive suite of tools for validating deployments, including health checks, functional testing, and security validation.
*   **Podman Compose Automation:** An automated system for managing containerized services, including health monitoring and auto-restarting.
*   **Phoenix Hydra System Review:** A comprehensive engine for discovering, analyzing, and assessing the entire system, providing a continuous feedback loop for improvement.

### 3. Non-Transformer AI and Local Processing

A key strategic initiative is the adoption of a non-transformer architecture for AI processing, enabling 100% local and offline capabilities.

*   **Mamba/SSM Models:** The use of State Space Models (SSM) for energy-efficient and high-performance AI processing.
*   **Local Inference Engine:** A local inference engine for executing AI models without relying on cloud services.
*   **Biomimetic Agents (RUBIK):** An advanced agent system with dynamic personas and evolutionary capabilities, running entirely on the local inference engine.

## Component Interaction

The components of the Phoenix Hydra system interact primarily through the **Event Routing** system.

1.  **Events are published** to the Event Router from various sources, including agent hooks, deployment validation tools, and the Podman Compose automation system.
2.  The **Pattern Matcher** identifies which subscribers are interested in each event based on their subscription patterns.
3.  The **Event Router delivers** the event to all matching subscribers, either synchronously or asynchronously.
4.  **Subscribers (e.g., agent hooks)** process the event and may perform actions, such as restarting a container, sending a notification, or publishing a new event.
5.  All events are **stored in the Event Store** for later analysis and replay.

This event-driven approach provides a highly scalable and resilient architecture, enabling the system to adapt and evolve over time.