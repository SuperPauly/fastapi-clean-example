"""
FastAPI Clean Architecture Template - Main Application Entry Point

This module serves as the main entry point for the FastAPI application,
following hexagonal architecture principles.
"""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

# Create FastAPI application instance
app = FastAPI(
    title="FastAPI Clean Architecture Template",
    description="A comprehensive FastAPI application template following Clean Architecture principles",
    version="2.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get("/")
async def root() -> dict[str, str]:
    """Root endpoint returning basic application information."""
    return {
        "message": "FastAPI Clean Architecture Template",
        "version": "2.1.0",
        "status": "running",
        "architecture": "hexagonal"
    }


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring and load balancers."""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "service": "fastapi-clean-example",
            "version": "2.1.0"
        }
    )


@app.get("/api/v1/status")
async def api_status() -> dict[str, str]:
    """API status endpoint."""
    return {
        "api_version": "v1",
        "status": "operational",
        "features": [
            "hexagonal_architecture",
            "clean_code_principles",
            "comprehensive_testing",
            "docker_support",
            "ci_cd_pipeline"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )

