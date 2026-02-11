"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.di.container import DIContainer
from src.presentation.api.routes import agent, auth
from src.presentation.api.schemas.response import ErrorResponse, HealthResponse

# Load environment variables
from dotenv import load_dotenv

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting AWS AI Agent API...")

    # Initialize DI container
    container = DIContainer()
    app.state.container = container

    yield

    # Shutdown
    print("👋 Shutting down AWS AI Agent API...")


# Create FastAPI application
app = FastAPI(
    title="AWS AI Agent API",
    description="AI agent solution for stock prices and financial document queries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    """Handle ValueError exceptions."""
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            timestamp=datetime.now(),
        ).model_dump(mode="json"),
    )


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    """Handle RuntimeError exceptions."""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            timestamp=datetime.now(),
        ).model_dump(mode="json"),
    )


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["health"],
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns the current status and timestamp of the API.
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="1.0.0",
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": "AWS AI Agent API",
        "version": "1.0.0",
        "description": "AI agent for stock prices and financial document queries",
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(auth.router)
app.include_router(agent.router)


# Middleware to inject dependencies
@app.middleware("http")
async def inject_dependencies(request: Request, call_next):
    """Inject dependencies into request state."""
    request.state.container = app.state.container
    response = await call_next(request)
    return response
