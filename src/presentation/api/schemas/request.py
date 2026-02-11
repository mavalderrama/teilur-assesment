"""Request schemas for the API."""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request schema for agent queries."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural language query for the AI agent",
        examples=["What is the stock price for Amazon right now?"],
    )

    stream: bool = Field(
        default=True,
        description="Whether to stream the response (default: True)",
    )


class AuthRequest(BaseModel):
    """Request schema for authentication."""

    username: str = Field(..., min_length=1, description="Cognito username")
    password: str = Field(..., min_length=8, description="User password")
