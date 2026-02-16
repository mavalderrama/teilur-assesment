"""FastAPI application entry point."""
import os
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse

from src.di.container import DIContainer
from src.infrastructure.logging import get_logger
from src.presentation.api.routes import agent, auth
from src.presentation.api.schemas.response import ErrorResponse, HealthResponse

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    environment = os.getenv("ENVIRONMENT", "production")
    aws_region = os.getenv("AWS_REGION", "us-east-1")

    logger.info(
        "Starting AWS AI Agent API",
        extra={
            "environment": environment,
            "aws_region": aws_region,
            "python_version": os.sys.version,
        },
    )

    try:
        # Initialize DI container
        container = DIContainer()
        app.state.container = container
        logger.info("Application startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to initialize application: {str(e)}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down AWS AI Agent API")


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
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.error(
        "Validation error occurred",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id,
        },
    )

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
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.error(
        "Runtime error occurred",
        extra={
            "error": str(exc),
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc),
            timestamp=datetime.now(),
        ).model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    correlation_id = getattr(request.state, "correlation_id", None)
    logger.error(
        "Unexpected error occurred",
        extra={
            "error": str(exc),
            "error_type": type(exc).__name__,
            "path": request.url.path,
            "method": request.method,
            "correlation_id": correlation_id,
        },
        exc_info=True,
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred",
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


# AgentCore health check endpoint (required by AgentCore - probes /ping)
@app.get("/ping", tags=["health"])
async def ping():
    """AgentCore health check endpoint."""
    return {"status": "healthy"}


# AgentCore invocation endpoint (required by AgentCore - sends to /invocations)
@app.post("/invocations", tags=["agentcore"])
async def invocations(request: Request):
    """
    AgentCore invocation endpoint.

    Accepts {"query": "...", "stream": true/false} and delegates to the agent orchestrator.
    Supports both streaming (SSE) and non-streaming responses.
    """
    from src.di.container import get_container
    from src.presentation.api.schemas.response import AgentStepResponse, QueryResponse
    from src.presentation.streaming.event_stream import EventStreamFormatter

    body = await request.json()
    prompt = body.get("query") or body.get("input", {}).get("prompt", "")
    stream = body.get("stream", False)
    if not prompt:
        return JSONResponse(status_code=400, content={"error": "No prompt provided"})

    try:
        container = get_container()
        orchestrator = container.agent_orchestrator

        if stream:
            event_stream = orchestrator.process_query_stream(prompt, user_id="agentcore-user")
            formatted_stream = EventStreamFormatter.stream_events(event_stream)

            return StreamingResponse(
                formatted_stream,
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                },
            )
        else:
            result = await orchestrator.process_query(prompt, user_id="agentcore-user")

            return QueryResponse(
                query=result.query,
                answer=result.answer,
                reasoning_steps=[
                    AgentStepResponse(
                        step_number=step.step_number,
                        action=step.action,
                        action_input=step.action_input,
                        observation=step.observation,
                        timestamp=step.timestamp,
                    )
                    for step in result.reasoning_steps
                ],
                sources=result.sources,
                execution_time_ms=result.execution_time_ms,
                timestamp=result.timestamp,
                trace_id=result.trace_id,
                trace_url=result.trace_url,
            )
    except Exception as e:
        logger.error(f"Invocation failed: {str(e)}", exc_info=True)
        return JSONResponse(status_code=500, content={"error": str(e)})


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


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Log all HTTP requests and responses with timing."""
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    # Log incoming request
    logger.info(
        "Incoming request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_host": request.client.host if request.client else None,
            "correlation_id": correlation_id,
        },
    )

    # Process request and measure time
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000  # Convert to ms

        # Log response
        logger.info(
            "Request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "process_time_ms": round(process_time, 2),
                "correlation_id": correlation_id,
            },
        )

        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        response.headers["X-Process-Time"] = str(round(process_time, 2))

        return response

    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(
            "Request failed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "error": str(e),
                "process_time_ms": round(process_time, 2),
                "correlation_id": correlation_id,
            },
            exc_info=True,
        )
        raise


# Middleware to inject dependencies
@app.middleware("http")
async def inject_dependencies(request: Request, call_next):
    """Inject dependencies into request state."""
    request.state.container = app.state.container
    response = await call_next(request)
    return response
