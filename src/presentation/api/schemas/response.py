"""Response schemas for the API."""
from datetime import datetime

from pydantic import BaseModel, Field


class AgentStepResponse(BaseModel):
    """Response schema for agent reasoning steps."""

    step_number: int
    action: str
    action_input: dict
    observation: str
    timestamp: datetime


class QueryResponse(BaseModel):
    """Response schema for agent queries (non-streaming)."""

    query: str
    answer: str
    reasoning_steps: list[AgentStepResponse]
    sources: list[str]
    execution_time_ms: float
    timestamp: datetime
    trace_id: str | None = None
    trace_url: str | None = None


class AuthResponse(BaseModel):
    """Response schema for authentication."""

    access_token: str = Field(..., description="JWT access token")
    id_token: str = Field(..., description="JWT ID token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Token expiration in seconds")


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(..., description="Server timestamp")
    version: str = Field(default="1.0.0", description="API version")


class ErrorResponse(BaseModel):
    """Response schema for errors."""

    error: str = Field(..., description="Error message")
    detail: str | None = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.now)
