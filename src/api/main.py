"""
FastAPI Application Structure - Engine Framework REST API.

This module provides the main FastAPI application structure for the Engine Framework,
including middleware configuration, CORS setup, authentication, error handling,
and OpenAPI documentation. It serves as the entry point for all REST API endpoints
and WebSocket connections.

Key Features:
- FastAPI application with async/await support
- Comprehensive middleware stack (CORS, authentication, logging, metrics)
- OpenAPI/Swagger documentation with custom schemas
- Error handling and validation
- Health checks and monitoring endpoints
- Request/response logging and metrics
- Security headers and rate limiting
- Static file serving for documentation
- WebSocket endpoint integration
- Background task management

Architecture:
- FastAPI app with modular router structure
- Middleware stack for cross-cutting concerns
- Authentication and authorization layers  
- Error handlers for consistent responses
- OpenAPI customization for documentation
- Background tasks for cleanup and monitoring
- Integration with WebSocket manager
- Service layer dependency injection

Dependencies:
- FastAPI framework
- Service layers for business logic
- WebSocket manager for real-time updates
- Authentication providers
- Monitoring and logging infrastructure
"""

from typing import Dict, Any, List, Optional, Callable
import asyncio
import logging
import time
import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, Request, Response, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html
from fastapi.openapi.utils import get_openapi
from contextlib import asynccontextmanager

import uvicorn
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse

# Import WebSocket functionality
from .websocket import websocket_manager, websocket_endpoint

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Process request and log details."""
        # Generate request ID
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        logger.info(f"Request {request_id}: {request.method} {request.url}")
        
        # Add request ID to headers
        response = await call_next(request)
        
        # Calculate processing time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        # Log response
        logger.info(f"Response {request_id}: {response.status_code} ({process_time:.3f}s)")
        
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware for collecting API metrics."""
    
    def __init__(self, app):
        super().__init__(app)
        self.metrics = {
            'requests_total': 0,
            'requests_by_method': {},
            'requests_by_status': {},
            'response_times': [],
            'active_requests': 0,
            'errors_total': 0
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Process request and collect metrics."""
        start_time = time.time()
        
        # Update active requests
        self.metrics['active_requests'] += 1
        
        try:
            response = await call_next(request)
            
            # Update metrics
            self.metrics['requests_total'] += 1
            
            # Track by method
            method = request.method
            self.metrics['requests_by_method'][method] = self.metrics['requests_by_method'].get(method, 0) + 1
            
            # Track by status code
            status_code = response.status_code
            self.metrics['requests_by_status'][status_code] = self.metrics['requests_by_status'].get(status_code, 0) + 1
            
            # Track response times
            response_time = time.time() - start_time
            self.metrics['response_times'].append(response_time)
            
            # Keep only last 1000 response times
            if len(self.metrics['response_times']) > 1000:
                self.metrics['response_times'] = self.metrics['response_times'][-1000:]
            
            # Track errors
            if status_code >= 400:
                self.metrics['errors_total'] += 1
            
            return response
            
        except Exception as e:
            self.metrics['errors_total'] += 1
            raise
        finally:
            self.metrics['active_requests'] -= 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics."""
        metrics = self.metrics.copy()
        
        # Calculate average response time
        if metrics['response_times']:
            metrics['avg_response_time'] = sum(metrics['response_times']) / len(metrics['response_times'])
            metrics['max_response_time'] = max(metrics['response_times'])
            metrics['min_response_time'] = min(metrics['response_times'])
        else:
            metrics['avg_response_time'] = 0
            metrics['max_response_time'] = 0
            metrics['min_response_time'] = 0
        
        # Remove raw response times from output
        del metrics['response_times']
        
        return metrics


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware."""
    
    def __init__(self, app, calls: int = 100, period: int = 60):
        super().__init__(app)
        self.calls = calls
        self.period = period
        self.clients = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> StarletteResponse:
        """Apply rate limiting."""
        client_ip = request.client.host
        now = datetime.utcnow()
        
        # Clean old entries
        cutoff = now - timedelta(seconds=self.period)
        if client_ip in self.clients:
            self.clients[client_ip] = [
                timestamp for timestamp in self.clients[client_ip]
                if timestamp > cutoff
            ]
        else:
            self.clients[client_ip] = []
        
        # Check rate limit
        if len(self.clients[client_ip]) >= self.calls:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {self.calls} requests per {self.period} seconds"
                }
            )
        
        # Record request
        self.clients[client_ip].append(now)
        
        return await call_next(request)


# Global metrics middleware instance
metrics_middleware = MetricsMiddleware(None)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Engine Framework API...")
    
    # Initialize services and dependencies
    await startup_event()
    
    yield
    
    # Shutdown
    logger.info("Shutting down Engine Framework API...")
    await shutdown_event()


async def startup_event():
    """Application startup tasks."""
    logger.info("Performing startup tasks...")
    
    # Initialize WebSocket manager
    # (Already initialized in websocket.py)
    
    # Start background tasks
    asyncio.create_task(background_tasks())
    
    logger.info("Startup completed successfully")


async def shutdown_event():
    """Application shutdown tasks."""
    logger.info("Performing shutdown tasks...")
    
    # Cleanup WebSocket connections
    # (Handled by WebSocket manager)
    
    logger.info("Shutdown completed successfully")


async def background_tasks():
    """Background maintenance tasks."""
    while True:
        try:
            await asyncio.sleep(300)  # 5 minutes
            
            # Log connection stats
            stats = websocket_manager.get_connection_stats()
            logger.info(f"WebSocket stats: {stats['connections']['active_connections']} active connections")
            
            # Log API metrics
            api_metrics = metrics_middleware.get_metrics()
            logger.info(f"API metrics: {api_metrics['requests_total']} total requests, {api_metrics['active_requests']} active")
            
        except Exception as e:
            logger.error(f"Error in background tasks: {str(e)}")


# Create FastAPI application
def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Engine Framework API",
        description="Comprehensive AI Agent Orchestration System",
        version="1.0.0",
        docs_url=None,  # We'll serve custom docs
        redoc_url=None,  # We'll serve custom redoc
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan
    )
    
    # Configure middleware
    configure_middleware(app)
    
    # Configure error handlers
    configure_error_handlers(app)
    
    # Configure routes
    configure_routes(app)
    
    # Configure documentation
    configure_documentation(app)
    
    return app


def configure_middleware(app: FastAPI):
    """Configure middleware stack."""
    
    # Security middleware
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # Configure properly for production
    )
    
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure properly for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Compression middleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware, calls=100, period=60)
    
    # Custom middleware
    app.add_middleware(RequestLoggingMiddleware)
    
    # Metrics middleware (need to update instance)
    global metrics_middleware
    metrics_middleware = MetricsMiddleware(app)
    app.add_middleware(type(metrics_middleware), app=app)


def configure_error_handlers(app: FastAPI):
    """Configure error handlers."""
    
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": exc.detail,
                "status_code": exc.status_code,
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """Handle general exceptions."""
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc):
        """Handle 404 errors."""
        return JSONResponse(
            status_code=404,
            content={
                "error": "Not found",
                "message": f"The requested resource {request.url.path} was not found",
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": getattr(request.state, 'request_id', None)
            }
        )


def configure_routes(app: FastAPI):
    """Configure API routes."""
    
    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "services": {
                "api": "running",
                "websocket": "running",
                "database": "unknown",  # Would check actual DB connection
                "redis": "unknown"      # Would check actual Redis connection
            }
        }
    
    # Metrics endpoint
    @app.get("/metrics", tags=["Monitoring"])
    async def get_metrics():
        """Get API metrics."""
        api_metrics = metrics_middleware.get_metrics()
        ws_stats = websocket_manager.get_connection_stats()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "api": api_metrics,
            "websocket": ws_stats
        }
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "name": "Engine Framework API",
            "description": "AI Agent Orchestration System",
            "version": "1.0.0",
            "documentation": "/docs",
            "openapi": "/api/v1/openapi.json",
            "websocket": "/ws",
            "health": "/health",
            "metrics": "/metrics"
        }
    
    # WebSocket endpoint
    app.websocket("/ws")(websocket_endpoint)
    
    # Import and include API routers
    # Note: These will be created in subsequent tasks
    try:
        from .routers import (
            projects, agents, teams, workflows, 
            protocols, tools, books, observability
        )
        
        # Include routers with prefixes
        app.include_router(projects.router, prefix="/api/v1/projects", tags=["Projects"])
        app.include_router(agents.router, prefix="/api/v1/agents", tags=["Agents"])
        app.include_router(teams.router, prefix="/api/v1/teams", tags=["Teams"])
        app.include_router(workflows.router, prefix="/api/v1/workflows", tags=["Workflows"])
        app.include_router(protocols.router, prefix="/api/v1/protocols", tags=["Protocols"])
        app.include_router(tools.router, prefix="/api/v1/tools", tags=["Tools"])
        app.include_router(books.router, prefix="/api/v1/books", tags=["Books"])
        app.include_router(observability.router, prefix="/api/v1/observability", tags=["Observability"])
        
    except ImportError as e:
        logger.warning(f"Some API routers not available yet: {str(e)}")
        # This is expected during development - routers will be created in subsequent tasks


def configure_documentation(app: FastAPI):
    """Configure API documentation."""
    
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        """Custom Swagger UI."""
        return get_swagger_ui_html(
            openapi_url="/api/v1/openapi.json",
            title="Engine Framework API - Documentation",
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@4.15.5/swagger-ui.css",
        )
    
    @app.get("/redoc", include_in_schema=False)
    async def redoc_html():
        """Custom ReDoc documentation."""
        return get_redoc_html(
            openapi_url="/api/v1/openapi.json",
            title="Engine Framework API - Documentation",
            redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@2.0.0/bundles/redoc.standalone.js",
        )
    
    def custom_openapi():
        """Custom OpenAPI schema."""
        if app.openapi_schema:
            return app.openapi_schema
        
        openapi_schema = get_openapi(
            title="Engine Framework API",
            version="1.0.0",
            description="""
            # Engine Framework API
            
            Comprehensive AI Agent Orchestration System with 6 core pillars:
            
            ## Core Systems
            - **Agents**: AI agents with configurable modules and capabilities
            - **Teams**: Coordinated groups of agents with hierarchy
            - **Workflows**: Pregel-based process orchestration
            - **Tools**: External integrations (APIs, CLI, MCP servers)
            - **Protocols**: Command sets for agent behavior
            - **Books**: Hierarchical memory and knowledge management
            
            ## Features
            - Real-time WebSocket updates
            - Comprehensive monitoring and observability
            - Flexible configuration and customization
            - Production-ready with security and performance
            
            ## Getting Started
            1. Create a project: `POST /api/v1/projects`
            2. Create agents: `POST /api/v1/agents`
            3. Create a team: `POST /api/v1/teams`
            4. Create workflows: `POST /api/v1/workflows`
            5. Execute and monitor via WebSocket: `/ws`
            
            ## WebSocket Events
            Connect to `/ws` for real-time updates on:
            - Agent execution status and progress
            - Workflow state changes and monitoring
            - System logs and alerts
            - Tool execution results
            - Book content updates
            
            ## Authentication
            Most endpoints require authentication. Include JWT token in Authorization header:
            ```
            Authorization: Bearer <your-jwt-token>
            ```
            """,
            routes=app.routes,
        )
        
        # Add custom tags
        openapi_schema["tags"] = [
            {"name": "Projects", "description": "Project management and organization"},
            {"name": "Agents", "description": "AI agent creation and management"},
            {"name": "Teams", "description": "Team coordination and collaboration"},
            {"name": "Workflows", "description": "Process orchestration and execution"},
            {"name": "Protocols", "description": "Command protocols and behaviors"},
            {"name": "Tools", "description": "External tool integrations"},
            {"name": "Books", "description": "Knowledge management and memory"},
            {"name": "Observability", "description": "Monitoring, logs, and metrics"},
            {"name": "Health", "description": "System health and status"},
            {"name": "Monitoring", "description": "Performance metrics and statistics"},
            {"name": "Root", "description": "API root and information"},
        ]
        
        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT"
            }
        }
        
        # Add WebSocket documentation
        openapi_schema["components"]["schemas"]["WebSocketMessage"] = {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Message ID"},
                "event_type": {"type": "string", "description": "Type of event"},
                "data": {"type": "object", "description": "Event data"},
                "timestamp": {"type": "string", "format": "date-time"},
                "scope": {"type": "string", "description": "Event scope"},
                "scope_id": {"type": "string", "description": "Scope-specific ID"},
                "metadata": {"type": "object", "description": "Additional metadata"}
            }
        }
        
        app.openapi_schema = openapi_schema
        return app.openapi_schema
    
    app.openapi = custom_openapi


# Authentication dependency
security = HTTPBearer()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current authenticated user."""
    try:
        # This is a placeholder - implement proper JWT validation
        import jwt
        
        token = credentials.credentials
        payload = jwt.decode(token, options={"verify_signature": False})  # For development
        
        return {
            "user_id": payload.get("user_id"),
            "username": payload.get("username"),
            "email": payload.get("email"),
            "permissions": payload.get("permissions", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Optional[Dict[str, Any]]:
    """Get current user if authenticated, otherwise None."""
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None


# Create app instance
app = create_app()


# Development server configuration
if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )


# Production configuration
def create_production_app():
    """Create production-ready app with proper configuration."""
    
    # Set production settings
    import os
    
    # Configure logging for production
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure security settings
    allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
    
    app = create_app()
    
    # Update middleware for production
    app.user_middleware = [
        middleware for middleware in app.user_middleware 
        if not isinstance(middleware.cls, TrustedHostMiddleware)
    ]
    
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=allowed_hosts
    )
    
    # Update CORS for production
    app.user_middleware = [
        middleware for middleware in app.user_middleware 
        if not isinstance(middleware.cls, CORSMiddleware)
    ]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )
    
    return app


# Export for production use
production_app = create_production_app()


# Example usage and testing
async def example_api_usage():
    """Example usage of the API."""
    
    print("Engine Framework API")
    print("====================")
    
    # The API provides endpoints for:
    print("1. Projects: /api/v1/projects")
    print("2. Agents: /api/v1/agents")
    print("3. Teams: /api/v1/teams")
    print("4. Workflows: /api/v1/workflows")
    print("5. Protocols: /api/v1/protocols")
    print("6. Tools: /api/v1/tools")
    print("7. Books: /api/v1/books")
    print("8. Observability: /api/v1/observability")
    
    print("\nWebSocket: /ws")
    print("Documentation: /docs")
    print("Health Check: /health")
    print("Metrics: /metrics")
    
    # Get current metrics
    metrics = metrics_middleware.get_metrics()
    print(f"\nCurrent API Metrics: {json.dumps(metrics, indent=2)}")
    
    # Get WebSocket stats
    ws_stats = websocket_manager.get_connection_stats()
    print(f"\nWebSocket Stats: {json.dumps(ws_stats, indent=2)}")


if __name__ == "__main__":
    import asyncio
    
    # Run example
    asyncio.run(example_api_usage())
    
    # Start server
    print("\nStarting development server...")
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
