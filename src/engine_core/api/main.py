"""
Engine Core FastAPI Application - Main REST API Application.

This module provides the main FastAPI application for the Engine Framework Core,
including middleware configuration, CORS setup, error handling, and router integration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi

from .routers.books import router as books_router
from .routers.agents import router as agents_router

# Create FastAPI application
app = FastAPI(
    title="Engine Core API",
    description="REST API for Engine Framework Core Components",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add GZip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include routers
app.include_router(books_router)
app.include_router(agents_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Overall health check for the API."""
    return {
        "service": "engine-core-api",
        "status": "healthy",
        "version": "1.0.0",
        "components": {
            "books": "healthy",
            "agents": "healthy"
        }
    }

# Custom OpenAPI schema
def custom_openapi():
    """Generate custom OpenAPI schema."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="Engine Core API",
        version="1.0.0",
        description="REST API for Engine Framework Core Components",
        routes=app.routes,
    )

    # Add custom schema components
    openapi_schema["components"]["schemas"].update({
        "ErrorResponse": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "default": False},
                "error_code": {"type": "string"},
                "error_message": {"type": "string"},
                "details": {"type": "object"}
            }
        }
    })

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    return JSONResponse(
        status_code=404,
        content={
            "success": False,
            "error_code": "NOT_FOUND",
            "error_message": "Resource not found",
            "details": {"path": str(request.url)}
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_code": "INTERNAL_ERROR",
            "error_message": "Internal server error",
            "details": {"error": str(exc)}
        }
    )