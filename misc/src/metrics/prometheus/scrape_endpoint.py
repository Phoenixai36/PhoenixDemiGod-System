"""
HTTP endpoint for Prometheus metrics scraping.
"""

import asyncio
import logging
from typing import Optional, Dict, Any, Callable
from datetime import datetime
import json

try:
    from aiohttp import web, ClientTimeout
    from aiohttp.web import Request, Response
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False
    web = None
    Request = None
    Response = None

from .registry import PrometheusRegistry, default_registry


class ScrapeEndpoint:
    """HTTP endpoint for serving Prometheus metrics."""
    
    def __init__(self, registry: Optional[PrometheusRegistry] = None,
                 host: str = "0.0.0.0", port: int = 8080):
        if not AIOHTTP_AVAILABLE:
            raise ImportError("aiohttp is required for ScrapeEndpoint. Install with: pip install aiohttp")
        
        self.registry = registry or default_registry
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        # Web application
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        
        # Statistics
        self.scrape_count = 0
        self.last_scrape_time: Optional[datetime] = None
        self.error_count = 0
        
        # Configuration
        self.include_timestamp = False
        self.include_help = True
        self.custom_headers: Dict[str, str] = {}
        
        # Setup routes
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        self.app.router.add_get('/metrics', self._metrics_handler)
        self.app.router.add_get('/health', self._health_handler)
        self.app.router.add_get('/stats', self._stats_handler)
        self.app.router.add_get('/', self._index_handler)
    
    async def _metrics_handler(self, request: Request) -> Response:
        """Handle /metrics endpoint for Prometheus scraping."""
        try:
            start_time = datetime.now()
            
            # Check for query parameters
            include_timestamp = request.query.get('timestamp', '').lower() in ('true', '1')
            include_help = request.query.get('help', 'true').lower() in ('true', '1')
            
            # Generate metrics output
            metrics_output = self.registry.generate_prometheus_output(
                include_timestamp=include_timestamp or self.include_timestamp,
                include_help=include_help and self.include_help
            )
            
            # Update statistics
            self.scrape_count += 1
            self.last_scrape_time = datetime.now()
            
            # Calculate generation time
            generation_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare headers
            headers = {
                'Content-Type': 'text/plain; version=0.0.4; charset=utf-8',
                'X-Metrics-Count': str(len(metrics_output.split('\n'))),
                'X-Generation-Time': f"{generation_time:.3f}s",
                **self.custom_headers
            }
            
            self.logger.debug(f"Served metrics scrape request in {generation_time:.3f}s")
            
            return Response(text=metrics_output, headers=headers)
            
        except Exception as e:
            self.error_count += 1
            self.logger.error(f"Error serving metrics: {str(e)}")
            
            return Response(
                text=f"# Error generating metrics: {str(e)}\n",
                status=500,
                headers={'Content-Type': 'text/plain'}
            )
    
    async def _health_handler(self, request: Request) -> Response:
        """Handle /health endpoint."""
        try:
            # Basic health check
            registry_stats = self.registry.get_registry_stats()
            
            health_status = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'metrics_count': registry_stats['total_metrics'],
                'collectors_count': registry_stats['registered_collectors'],
                'scrape_count': self.scrape_count,
                'error_count': self.error_count,
                'last_scrape': self.last_scrape_time.isoformat() if self.last_scrape_time else None
            }
            
            # Check for issues
            validation_issues = self.registry.validate_output()
            if validation_issues:
                health_status['status'] = 'degraded'
                health_status['issues'] = validation_issues
            
            status_code = 200 if health_status['status'] == 'healthy' else 503
            
            return Response(
                text=json.dumps(health_status, indent=2),
                status=status_code,
                headers={'Content-Type': 'application/json'}
            )
            
        except Exception as e:
            self.logger.error(f"Error in health check: {str(e)}")
            
            return Response(
                text=json.dumps({
                    'status': 'unhealthy',
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }),
                status=500,
                headers={'Content-Type': 'application/json'}
            )
    
    async def _stats_handler(self, request: Request) -> Response:
        """Handle /stats endpoint for detailed statistics."""
        try:
            registry_stats = self.registry.get_registry_stats()
            
            endpoint_stats = {
                'endpoint': {
                    'host': self.host,
                    'port': self.port,
                    'scrape_count': self.scrape_count,
                    'error_count': self.error_count,
                    'last_scrape_time': self.last_scrape_time.isoformat() if self.last_scrape_time else None,
                    'include_timestamp': self.include_timestamp,
                    'include_help': self.include_help
                },
                'registry': registry_stats
            }
            
            return Response(
                text=json.dumps(endpoint_stats, indent=2),
                headers={'Content-Type': 'application/json'}
            )
            
        except Exception as e:
            self.logger.error(f"Error getting stats: {str(e)}")
            
            return Response(
                text=json.dumps({'error': str(e)}),
                status=500,
                headers={'Content-Type': 'application/json'}
            )
    
    async def _index_handler(self, request: Request) -> Response:
        """Handle root endpoint with basic information."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Prometheus Metrics Exporter</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .endpoint {{ margin: 20px 0; padding: 10px; background: #f5f5f5; }}
                .stats {{ margin: 10px 0; }}
            </style>
        </head>
        <body>
            <h1>Prometheus Metrics Exporter</h1>
            <p>This endpoint serves metrics in Prometheus exposition format.</p>
            
            <div class="endpoint">
                <h3>Available Endpoints:</h3>
                <ul>
                    <li><a href="/metrics">/metrics</a> - Prometheus metrics (main scrape endpoint)</li>
                    <li><a href="/health">/health</a> - Health check</li>
                    <li><a href="/stats">/stats</a> - Detailed statistics</li>
                </ul>
            </div>
            
            <div class="stats">
                <h3>Quick Stats:</h3>
                <p>Scrapes served: {self.scrape_count}</p>
                <p>Errors: {self.error_count}</p>
                <p>Last scrape: {self.last_scrape_time or 'Never'}</p>
            </div>
            
            <div class="endpoint">
                <h3>Query Parameters for /metrics:</h3>
                <ul>
                    <li><code>?timestamp=true</code> - Include timestamps</li>
                    <li><code>?help=false</code> - Exclude HELP and TYPE comments</li>
                </ul>
            </div>
        </body>
        </html>
        """
        
        return Response(text=html_content, headers={'Content-Type': 'text/html'})
    
    async def start(self) -> bool:
        """Start the HTTP server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, self.host, self.port)
            await self.site.start()
            
            self.logger.info(f"Prometheus scrape endpoint started on http://{self.host}:{self.port}")
            self.logger.info(f"Metrics available at: http://{self.host}:{self.port}/metrics")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start scrape endpoint: {str(e)}")
            return False
    
    async def stop(self) -> None:
        """Stop the HTTP server."""
        try:
            if self.site:
                await self.site.stop()
                self.site = None
            
            if self.runner:
                await self.runner.cleanup()
                self.runner = None
            
            self.logger.info("Prometheus scrape endpoint stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping scrape endpoint: {str(e)}")
    
    def configure(self, config: Dict[str, Any]) -> None:
        """
        Configure the scrape endpoint.
        
        Args:
            config: Configuration dictionary
        """
        if 'include_timestamp' in config:
            self.include_timestamp = config['include_timestamp']
        
        if 'include_help' in config:
            self.include_help = config['include_help']
        
        if 'custom_headers' in config:
            self.custom_headers = config['custom_headers']
        
        self.logger.info(f"Scrape endpoint configured: {config}")
    
    def add_custom_header(self, name: str, value: str) -> None:
        """Add a custom header to all responses."""
        self.custom_headers[name] = value
    
    def remove_custom_header(self, name: str) -> bool:
        """Remove a custom header."""
        if name in self.custom_headers:
            del self.custom_headers[name]
            return True
        return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


class SimpleScrapeEndpoint:
    """Simplified scrape endpoint without aiohttp dependency."""
    
    def __init__(self, registry: Optional[PrometheusRegistry] = None):
        self.registry = registry or default_registry
        self.logger = logging.getLogger(__name__)
    
    def get_metrics_text(self, include_timestamp: bool = False,
                        include_help: bool = True) -> str:
        """Get metrics in Prometheus text format."""
        return self.registry.generate_prometheus_output(
            include_timestamp=include_timestamp,
            include_help=include_help
        )
    
    def save_metrics_to_file(self, file_path: str, 
                           include_timestamp: bool = False) -> bool:
        """Save current metrics to a file."""
        return self.registry.export_to_file(file_path, include_timestamp)