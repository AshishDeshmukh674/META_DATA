"""
FastAPI Application Factory.

This is the main entry point for the Lakehouse Explorer API.
It creates the FastAPI app with middleware, CORS, error handlers, and routers.

Why Application Factory Pattern?
- Clean separation of concerns
- Easy to test (can create app instances with different configs)
- Middleware can be applied in correct order
- Startup/shutdown events centralized
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import time

from app.core.settings import settings
from app.core.logger import get_logger, generate_request_id

# Initialize logger
logger = get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan events.
    
    Runs on startup and shutdown:
    - Startup: Initialize connections, log app start
    - Shutdown: Cleanup resources, close connections
    """
    # === STARTUP ===
    logger.info(
        "Starting Lakehouse Explorer API",
        extra={
            "version": settings.app_version,
            "environment": settings.environment,
            "mcp_enabled": settings.enable_mcp,
        }
    )
    
    yield
    
    # === SHUTDOWN ===
    logger.info("Shutting down Lakehouse Explorer API")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        Configured FastAPI instance
    """
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Metastore-less Lakehouse Explorer & SQL Platform\n\n"
            "Discover and query Delta, Iceberg, Hudi, and Parquet tables "
            "directly from S3/MinIO without a metastore."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # ===== MIDDLEWARE (Applied in reverse order) =====
    
    # 1. CORS - Allow frontend to call API
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.get_allowed_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 2. Trusted Host - Security (only in production)
    if settings.is_production():
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=settings.get_allowed_origins_list(),
        )
    
    # 3. Request ID & Logging Middleware
    @app.middleware("http")
    async def add_request_id_and_logging(request: Request, call_next):
        """
        Add unique request ID to every request and log request/response.
        
        Request ID is available as: request.state.request_id
        """
        # Generate unique request ID
        request_id = generate_request_id()
        request.state.request_id = request_id
        
        # Log incoming request
        start_time = time.time()
        logger.info(
            "Incoming request",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host if request.client else None,
            }
        )
        
        # Process request
        response = await call_next(request)
        
        # Log response
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Request completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            }
        )
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response
    
    # ===== EXCEPTION HANDLERS =====
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with detailed messages."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.error(
            "Validation error",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "errors": exc.errors(),
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "detail": exc.errors(),
                "request_id": request_id,
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected errors gracefully."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        logger.exception(
            "Unhandled exception",
            extra={
                "request_id": request_id,
                "path": request.url.path,
                "exception_type": type(exc).__name__,
            }
        )
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": str(exc) if settings.is_development() else "An unexpected error occurred",
                "request_id": request_id,
            }
        )
    
    # ===== ROUTERS =====
    from app.api import health, connection, detect, metadata, metadata_gen, query
    app.include_router(health.router, prefix="/health", tags=["Health"])
    app.include_router(connection.router, prefix="/connect", tags=["Connection"])
    app.include_router(detect.router, prefix="/detect-format", tags=["Detection"])
    app.include_router(metadata.router, tags=["Metadata (Phase 5)"])  # prefix="/metadata" already in router
    app.include_router(metadata_gen.router, tags=["Metadata Generation (Phase 6)"])  # prefix="/metadata" already in router
    app.include_router(query.router, tags=["Query (Phase 8)"])  # prefix="/query" already in router
    
    return app


# Create application instance
app = create_application()


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint - API information.
    
    Returns basic information about the API.
    """
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": "/docs",
        "health": "/health",
    }
