"""
Health Check API Router.

Provides endpoints to check system health and readiness.
Used by load balancers, monitoring systems, and debugging.

Why Health Checks?
- Load balancers know if service is up
- Monitoring systems can alert on failures
- Debugging tool to check dependencies
- Kubernetes liveness/readiness probes
"""

from fastapi import APIRouter, status
from datetime import datetime
import sys
import platform

from app.core.settings import settings
from app.core.logger import get_logger

logger = get_logger()
router = APIRouter()


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    summary="Basic health check",
    response_description="Returns OK if service is running"
)
async def health_check():
    """
    Simple health check endpoint.
    
    Returns 200 OK if the service is running.
    Used by load balancers and container orchestrators.
    
    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "service": settings.app_name,
        "version": settings.app_version,
    }


@router.get(
    "/detailed",
    status_code=status.HTTP_200_OK,
    summary="Detailed health check",
    response_description="Returns detailed system information"
)
async def detailed_health_check():
    """
    Detailed health check with system information.
    
    Provides comprehensive system status including:
    - Application info
    - Python environment
    - System info
    - Feature flags
    - Configuration status
    
    Returns:
        dict: Detailed health status
    """
    
    # Check if dependencies are configured
    checks = {
        "aws_configured": settings.aws_access_key_id is not None,
        "minio_configured": bool(settings.minio_endpoint),
        "trino_configured": bool(settings.trino_host),
        "spark_configured": bool(settings.spark_master),
        "mcp_enabled": settings.enable_mcp,
    }
    
    # Overall health status
    overall_status = "healthy" if all([
        checks["minio_configured"] or checks["aws_configured"],
        checks["trino_configured"],
        checks["spark_configured"],
    ]) else "degraded"
    
    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        
        # Application info
        "application": {
            "name": settings.app_name,
            "version": settings.app_version,
            "environment": settings.environment,
        },
        
        # Python environment
        "python": {
            "version": sys.version,
            "executable": sys.executable,
        },
        
        # System info
        "system": {
            "platform": platform.platform(),
            "processor": platform.processor(),
            "python_implementation": platform.python_implementation(),
        },
        
        # Component status
        "components": checks,
        
        # Feature flags
        "features": {
            "mcp": settings.enable_mcp,
            "llm": settings.enable_llm,
            "metrics": settings.enable_metrics,
        },
    }


@router.get(
    "/ready",
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    response_description="Returns 200 if ready to serve traffic"
)
async def readiness_check():
    """
    Readiness probe for Kubernetes.
    
    Returns 200 if the service is ready to accept traffic.
    Checks that critical dependencies are configured.
    
    Returns:
        dict: Readiness status
    """
    
    # Check if at least one storage backend is configured
    storage_ready = (
        settings.aws_access_key_id is not None or
        settings.minio_endpoint is not None
    )
    
    # Check if query engines are configured
    engines_ready = (
        settings.trino_host is not None and
        settings.spark_master is not None
    )
    
    is_ready = storage_ready and engines_ready
    
    return {
        "ready": is_ready,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "storage": storage_ready,
            "engines": engines_ready,
        }
    }


@router.get(
    "/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    response_description="Returns 200 if service is alive"
)
async def liveness_check():
    """
    Liveness probe for Kubernetes.
    
    Returns 200 if the service process is alive.
    If this fails, Kubernetes will restart the pod.
    
    Returns:
        dict: Liveness status
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
