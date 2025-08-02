#!/usr/bin/env python3
"""
RUBIK Agent Service

A lightweight service that provides an HTTP API for the RUBIK biomimetic agent system.
This service acts as a gateway to the Phoenix Hydra RUBIK ecosystem, providing
health checks, status monitoring, and basic agent interaction capabilities.
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import psutil
import structlog
from aiohttp import ClientSession, web
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('rubik_agent_requests_total', 'Total requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('rubik_agent_request_duration_seconds', 'Request duration')
ACTIVE_AGENTS = Gauge('rubik_agent_active_agents', 'Number of active agents')
SYSTEM_MEMORY = Gauge('rubik_agent_system_memory_bytes', 'System memory usage')
SYSTEM_CPU = Gauge('rubik_agent_system_cpu_percent', 'System CPU usage')


class RubikAgentService:
    """
    RUBIK Agent Service - HTTP API gateway for the biomimetic agent system.
    """
    
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.app = web.Application()
        self.start_time = time.time()
        self.request_count = 0
        self.setup_routes()
        
        # Service status
        self.status = {
            "service": "rubik-agent",
            "version": "1.0.0",
            "status": "initializing",
            "start_time": datetime.utcnow().isoformat(),
            "ecosystem_connected": False,
            "active_agents": 0
        }
        
        logger.info("RUBIK Agent Service initialized", 
                   host=host, port=port)
    
    def setup_routes(self):
        """Setup HTTP routes for the service."""
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/status', self.get_status)
        self.app.router.add_get('/metrics', self.get_metrics)
        self.app.router.add_get('/agents', self.list_agents)
        self.app.router.add_post('/agents/task', self.submit_task)
        self.app.router.add_get('/ecosystem/status', self.ecosystem_status)
        self.app.router.add_get('/', self.root_handler)
    
    async def health_check(self, request: web.Request) -> web.Response:
        """Health check endpoint for container orchestration."""
        REQUEST_COUNT.labels(method='GET', endpoint='/health').inc()
        
        with REQUEST_DURATION.time():
            # Basic health checks
            health_status = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "uptime_seconds": time.time() - self.start_time,
                "memory_usage": psutil.virtual_memory().percent,
                "cpu_usage": psutil.cpu_percent(interval=1),
                "disk_usage": psutil.disk_usage('/').percent
            }
            
            # Update Prometheus metrics
            SYSTEM_MEMORY.set(psutil.virtual_memory().used)
            SYSTEM_CPU.set(psutil.cpu_percent())
            
            # Check if service is overloaded
            if health_status["memory_usage"] > 90 or health_status["cpu_usage"] > 95:
                health_status["status"] = "degraded"
                logger.warning("Service performance degraded", 
                             memory=health_status["memory_usage"],
                             cpu=health_status["cpu_usage"])
            
            status_code = 200 if health_status["status"] == "healthy" else 503
            
            logger.info("Health check performed", 
                       status=health_status["status"],
                       memory=health_status["memory_usage"],
                       cpu=health_status["cpu_usage"])
            
            return web.json_response(health_status, status=status_code)
    
    async def get_status(self, request: web.Request) -> web.Response:
        """Get detailed service status."""
        REQUEST_COUNT.labels(method='GET', endpoint='/status').inc()
        
        with REQUEST_DURATION.time():
            self.status.update({
                "uptime_seconds": time.time() - self.start_time,
                "request_count": self.request_count,
                "memory_usage_mb": psutil.Process().memory_info().rss / 1024 / 1024,
                "cpu_percent": psutil.Process().cpu_percent(),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.info("Status requested", status=self.status)
            return web.json_response(self.status)
    
    async def get_metrics(self, request: web.Request) -> web.Response:
        """Prometheus metrics endpoint."""
        REQUEST_COUNT.labels(method='GET', endpoint='/metrics').inc()
        
        # Update active agents metric (placeholder)
        ACTIVE_AGENTS.set(self.status.get("active_agents", 0))
        
        metrics_data = generate_latest()
        return web.Response(text=metrics_data.decode('utf-8'), 
                          content_type='text/plain')
    
    async def list_agents(self, request: web.Request) -> web.Response:
        """List active RUBIK agents (placeholder implementation)."""
        REQUEST_COUNT.labels(method='GET', endpoint='/agents').inc()
        
        with REQUEST_DURATION.time():
            # Placeholder agent data
            agents = [
                {
                    "agent_id": "rubik_001",
                    "archetype": "explorer",
                    "status": "active",
                    "fitness_score": 0.85,
                    "generation": 1,
                    "age_cycles": 42,
                    "current_mood": "curious",
                    "last_task": "system_analysis",
                    "created_at": datetime.utcnow().isoformat()
                },
                {
                    "agent_id": "rubik_002", 
                    "archetype": "guardian",
                    "status": "active",
                    "fitness_score": 0.92,
                    "generation": 2,
                    "age_cycles": 28,
                    "current_mood": "vigilant",
                    "last_task": "security_scan",
                    "created_at": datetime.utcnow().isoformat()
                }
            ]
            
            response = {
                "total_agents": len(agents),
                "active_agents": len([a for a in agents if a["status"] == "active"]),
                "agents": agents,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Agent list requested", total_agents=len(agents))
            return web.json_response(response)
    
    async def submit_task(self, request: web.Request) -> web.Response:
        """Submit a task to the RUBIK ecosystem (placeholder implementation)."""
        REQUEST_COUNT.labels(method='POST', endpoint='/agents/task').inc()
        
        with REQUEST_DURATION.time():
            try:
                task_data = await request.json()
                
                # Validate task data
                required_fields = ["task_type", "input_data"]
                for field in required_fields:
                    if field not in task_data:
                        return web.json_response(
                            {"error": f"Missing required field: {field}"},
                            status=400
                        )
                
                # Simulate task processing
                task_id = f"task_{int(time.time())}"
                
                response = {
                    "task_id": task_id,
                    "status": "accepted",
                    "task_type": task_data["task_type"],
                    "estimated_completion": "30s",
                    "assigned_agent": "rubik_001",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info("Task submitted", 
                           task_id=task_id,
                           task_type=task_data["task_type"])
                
                return web.json_response(response, status=202)
                
            except json.JSONDecodeError:
                return web.json_response(
                    {"error": "Invalid JSON in request body"},
                    status=400
                )
            except Exception as e:
                logger.error("Task submission failed", error=str(e))
                return web.json_response(
                    {"error": "Internal server error"},
                    status=500
                )
    
    async def ecosystem_status(self, request: web.Request) -> web.Response:
        """Get RUBIK ecosystem status (placeholder implementation)."""
        REQUEST_COUNT.labels(method='GET', endpoint='/ecosystem/status').inc()
        
        with REQUEST_DURATION.time():
            ecosystem_status = {
                "ecosystem_id": "phoenix_rubik_001",
                "status": "running",
                "population": {
                    "total_agents": 15,
                    "active_agents": 12,
                    "generation": 3,
                    "average_fitness": 0.78
                },
                "task_metrics": {
                    "total_processed": 1247,
                    "success_rate": 0.94,
                    "average_processing_time": 2.3
                },
                "learning": {
                    "knowledge_fragments": 892,
                    "learning_experiences": 456,
                    "evolution_cycles": 8
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info("Ecosystem status requested")
            return web.json_response(ecosystem_status)
    
    async def root_handler(self, request: web.Request) -> web.Response:
        """Root endpoint with service information."""
        REQUEST_COUNT.labels(method='GET', endpoint='/').inc()
        
        info = {
            "service": "RUBIK Agent Service",
            "description": "HTTP API gateway for Phoenix Hydra RUBIK biomimetic agent system",
            "version": "1.0.0",
            "endpoints": [
                "GET /health - Health check",
                "GET /status - Service status",
                "GET /metrics - Prometheus metrics",
                "GET /agents - List active agents",
                "POST /agents/task - Submit task to ecosystem",
                "GET /ecosystem/status - Ecosystem status"
            ],
            "documentation": "https://github.com/phoenix-hydra/docs",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return web.json_response(info)
    
    async def start(self):
        """Start the HTTP server."""
        self.status["status"] = "running"
        
        logger.info("Starting RUBIK Agent Service", 
                   host=self.host, port=self.port)
        
        runner = web.AppRunner(self.app)
        await runner.setup()
        
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        
        logger.info("RUBIK Agent Service started successfully",
                   host=self.host, port=self.port)
        
        return runner
    
    async def stop(self, runner):
        """Stop the HTTP server."""
        self.status["status"] = "stopping"
        logger.info("Stopping RUBIK Agent Service")
        
        await runner.cleanup()
        
        self.status["status"] = "stopped"
        logger.info("RUBIK Agent Service stopped")


async def main():
    """Main entry point for the RUBIK Agent Service."""
    # Configuration from environment variables
    host = os.getenv("RUBIK_AGENT_HOST", "0.0.0.0")
    port = int(os.getenv("RUBIK_AGENT_PORT", "8080"))
    
    # Create and start service
    service = RubikAgentService(host=host, port=port)
    runner = await service.start()
    
    try:
        # Keep the service running
        logger.info("RUBIK Agent Service is running. Press Ctrl+C to stop.")
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop(runner)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error("Service failed to start", error=str(e))
        sys.exit(1)