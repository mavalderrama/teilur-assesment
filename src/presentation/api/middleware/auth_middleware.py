"""Authentication middleware for FastAPI."""
import os
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.di.container import get_cognito_service
from src.infrastructure.logging import get_logger

security = HTTPBearer(auto_error=False)  # Don't auto-error for dev mode
logger = get_logger(__name__)


async def verify_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    cognito_service = Depends(get_cognito_service),
) -> dict[str, Any]:
    """
    Verify JWT token from Cognito.

    In development mode (ENVIRONMENT=development), bypasses authentication.

    Args:
        credentials: Authorization credentials with Bearer token
        cognito_service: Cognito authentication service

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    environment = os.getenv("ENVIRONMENT", "production")

    # Development mode - bypass authentication
    if environment == "development":
        logger.warning("Development mode: Bypassing authentication")
        return {
            "sub": "dev-user-123",
            "email": "dev@example.com",
            "username": "dev-user",
        }

    # Production mode - verify token
    if not credentials:
        logger.warning("Authentication failed: No credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        token = credentials.credentials
        claims = await cognito_service.verify_token(token)
        return claims

    except ValueError as e:
        logger.warning(f"Token verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_user_id(claims: dict[str, Any] = Depends(verify_token)) -> str:
    """
    Extract user ID from token claims.

    Args:
        claims: Decoded JWT claims

    Returns:
        User ID (sub claim)

    Raises:
        HTTPException: If user ID not found in claims
    """
    user_id = claims.get("sub")
    if not user_id:
        logger.error("User ID not found in token claims", extra={"claims": claims})
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token claims",
        )

    logger.debug("User authenticated", extra={"user_id": user_id})
    return user_id
