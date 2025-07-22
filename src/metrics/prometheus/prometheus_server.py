"""
Prometheus HTTP server for metrics scraping.

This module provides an HTTP server that exposes metrics in Prometheus format
for scraping by Prometheus servers.
"""

import logging
import asyncio
from typing import Optional, Dict, Any, Callable
from datetime import datetime

try:
    from fastapi import FastAPI, Response, HTTPException, Depends
    from fastapi.responses import PlainTextResponse
    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False

from .prometheus_exporter import PrometheusExporter


class PrometheusServer:
    """HTTP server for Prometheus metrics scraping."""
    
    def __init__(self, exporter: PrometheusExporter, port: int = 8000, host: str = "0.0.0.0"):
        if not FASTAPI_AVAILABLE:
            raise ImportError("FastAPI is required for PrometheusServer. Install with: pip install fastapi uvicorn")
        
        self.exporter = exporter
        self.port = port
        self.host = host
        self.logger = logging.getLogger(__name__)
        
        # Server state
        self._server_task: Optional[asyncio.Task] = None
        self._running = False
        
        # Statistics
        self.stats = {
            "requests_total": 0,
            "requests_errors": 0,
            "last_scrape_time": None,
            "last_scrape_duration": 0.0,
            "start_time": None
        }
        
        # Create FastAPI app
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create FastAPI application with metrics endpoints."""
        app = FastAPI(
            title="System Health Monitor - Prometheus Exporter",
            description="Prometheus metrics endpoint for system health monitoring",
            version="1.0.0"
        )
        
        @app.get("/metrics", response_class=PlainTextResponse)
        async def get_metrics():
            """Main Prometheus metrics endpoint."""
            return await self._handle_metrics_request()
        
        @app.get("/metrics/{metric_family}", response_class=PlainTextResponse)
        async def get_metric_family(metric_family: str):
            """Get specific metric family."""
            return await self._handle_family_request(metric_family)
        
        @app.get("/health")
        async def health_check():
            """Health check endpoint."""
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "uptime_seconds": (datetime.now() - self.stats["start_time"]).total_seconds() if self.stats["start_time"] else 0,
                "requests_total": self.stats["requests_total"],
                "requests_errors": self.stats["requests_errors"]
            }
        
        @app.get("/")
        async def root():
            """Root endpoint with information."""
            return {
                "service": "System Health Monitor - Prometheus Exporter",
                "endpoints": {
                    "/metrics": "Prometheus metrics endpoint",
                    "/metrics/{family}": "Specific metric family",
                    "/health": "Health check",
                    "/stats": "Server statistics"
                },
                "prometheus_scrape_url": f"http://{self.host}:{self.port}/metrics"
            }
        
        @app.get("/stats")
        async def get_stats():
            """Get server statistics."""
            stats = self.stats.copy()
            if stats["start_time"]:
                stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
                stats["start_time"] = stats["start_time"].isoformat()
            if stats["last_scrape_time"]:
                stats["last_scrape_time"] = stats["last_scrape_time"].isoformat()
            return stats
        
        return app
    
    async def _handle_metrics_request(self) -> str:
        """Handle metrics request with error handling and statistics."""
        start_time = datetime.now()
        
        try:
            self.stats["requests_total"] += 1
            
            # Export metrics
            metrics_output = await self.exporter.export_metrics()
            
            # Update statistics
            duration = (datetime.now() - start_time).total_seconds()
            self.stats["last_scrape_time"] = start_time
            self.stats["last_scrape_duration"] = duration
            
            self.logger.debug(f"Served metrics request in {duration:.3f}s")
            return metrics_output
            
        except Exception as e:
            self.stats["requests_errors"] += 1
            self.logger.error(f"Error serving metrics: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating metrics: {str(e)}")
    
    async def _handle_family_request(self, metric_family: str) -> str:
        """Handle specific metric family request."""
        start_time = datetime.now()
        
        try:
            self.stats["requests_total"] += 1
            
            # Export specific metric family
            family_output = await self.exporter.export_metric_family(metric_family)
            
            # Update statistics
            duration = (datetime.now() - start_time).total_seconds()
            self.stats["last_scrape_time"] = start_time
            self.stats["last_scrape_duration"] = duration
            
            self.logger.debug(f"Served metric family {metric_family} in {duration:.3f}s")
            return family_output
            
        except Exception as e:
            self.stats["requests_errors"] += 1
            self.logger.error(f"Error serving metric family {metric_family}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error generating metric family: {str(e)}")
    
    async def start(self) -> None:
        """Start the Prometheus server."""
        if self._running:
            self.logger.warning("Server is already running")
            return
        
        try:
            import uvicorn
            
            self.stats["start_time"] = datetime.now()
            self._running = True
            
            # Configure uvicorn
            config = uvicorn.Config(
                app=self.app,
                host=self.host,
                port=self.port,
                log_level="info",
                access_log=True
            )
            
            server = uvicorn.Server(config)
            
            # Start server in background task
            self._server_task = asyncio.create_task(server.serve())
            
            self.logger.info(f"Prometheus server started on http://{self.host}:{self.port}")
            self.logger.info(f"Metrics endpoint: http://{self.host}:{self.port}/metrics")
            
        except ImportError:
            raise ImportError("uvicorn is required for PrometheusServer. Install with: pip install uvicorn")
        except Exception as e:
            self._running = False
            self.logger.error(f"Failed to start Prometheus server: {str(e)}")
            raise
    
    async def stop(self) -> None:
        """Stop the Prometheus server."""
        if not self._running:
            return
        
        self._running = False
        
        if self._server_task:
            self._server_task.cancel()
            try:
                await self._server_task
            except asyncio.CancelledError:
                pass
        
        self.logger.info("Prometheus server stopped")
    
    def is_running(self) -> bool:
        """Check if the server is running."""
        return self._running
    
    def get_metrics_url(self) -> str:
        """Get the metrics endpoint URL."""
        return f"http://{self.host}:{self.port}/metrics"
    
    def get_stats(self) -> Dict[str, Any]:
        """Get server statistics."""
        stats = self.stats.copy()
        if stats["start_time"]:
            stats["uptime_seconds"] = (datetime.now() - stats["start_time"]).total_seconds()
        return stats


def create_prometheus_app(exporter: PrometheusExporter) -> FastAPI:
    """Create a standalone FastAPI app for Prometheus metrics."""
    if not FASTAPI_AVAILABLE:
        raise ImportError("FastAPI is required. Install with: pip install fastapi")
    
    app = FastAPI(
        title="Prometheus Metrics Exporter",
        description="Prometheus-compatible metrics endpoint",
        version="1.0.0"
    )
    
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        """Prometheus metrics endpoint."""
        try:
            return await exporter.export_metrics()
        except Exception as e:
            logging.getLogger(__name__).error(f"Error exporting metrics: {str(e)}")
            raise HTTPException(status_code=500, detail="Error generating metrics")
    
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "timestamp": datetime.now().isoformat()}
    
    return app


class PrometheusMiddleware:
    """Middleware for adding Prometheus metrics to existing FastAPI apps."""
    
    def __init__(self, exporter: PrometheusExporter, metrics_path: str = "/metrics"):
        self.exporter = exporter
        self.metrics_path = metrics_path
        self.logger = logging.getLogger(__name__)
    
    def add_to_app(self, app: FastAPI) -> None:
        """Add Prometheus endpoints to an existing FastAPI app."""
        
        @app.get(self.metrics_path, response_class=PlainTextResponse)
        async def prometheus_metrics():
            """Prometheus metrics endpoint."""
            try:
                return await self.exporter.export_metrics()
            except Exception as e:
                self.logger.error(f"Error exporting metrics: {str(e)}")
                raise HTTPException(status_code=500, detail="Error generating metrics")
        
        self.logger.info(f"Added Prometheus metrics endpoint at {self.metrics_path}")


# Convenience functions
async def start_prometheus_server(exporter: PrometheusExporter, 
                                port: int = 8000, 
                                host: str = "0.0.0.0") -> PrometheusServer:
    """Start a Prometheus server with the given exporter."""
    server = PrometheusServer(exporter, port, host)
    await server.start()
    return server


def add_prometheus_metrics(app: FastAPI, 
                         exporter: PrometheusExporter, 
                         metrics_path: str = "/metrics") -> None:
    """Add Prometheus metrics endpoint to an existing FastAPI app."""
    middleware = PrometheusMiddleware(exporter, metrics_path)
    middleware.add_to_app(app)