"""
Main FastAPI application for System Health Monitor.

This module provides the main FastAPI application with all endpoints.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import uvicorn
import asyncio
from pathlib import Path

from dashboard.api import router as dashboard_router, get_dashboard_service
from metrics.api.endpoints import router as metrics_router
from containers.api import router as containers_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("Starting System Health Monitor...")
    
    # Initialize dashboard service
    dashboard_service = await get_dashboard_service()
    print("Dashboard service initialized")
    
    yield
    
    # Shutdown
    print("Shutting down System Health Monitor...")
    await dashboard_service.shutdown()
    print("Shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="System Health Monitor",
    description="Container monitoring and health management system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(dashboard_router)

# Try to include other routers if they exist
try:
    app.include_router(metrics_router)
except ImportError:
    print("Metrics router not available")

try:
    app.include_router(containers_router)
except ImportError:
    print("Containers router not available")

# Serve static files if directory exists
static_dir = Path("src/frontend/static")
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "System Health Monitor API",
        "version": "1.0.0",
        "endpoints": {
            "dashboard": "/api/dashboard/",
            "dashboard_ui": "/api/dashboard/ui",
            "metrics": "/api/metrics/",
            "containers": "/api/containers/",
            "docs": "/docs",
            "health": "/health"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        # Check dashboard service
        dashboard_service = await get_dashboard_service()
        dashboard_healthy = dashboard_service.is_running
        
        return {
            "status": "healthy" if dashboard_healthy else "unhealthy",
            "services": {
                "dashboard": "healthy" if dashboard_healthy else "unhealthy"
            },
            "timestamp": "2025-07-20T16:00:00Z"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
