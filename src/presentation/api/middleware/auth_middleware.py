"""Authentication middleware for FastAPI."""
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.infrastructure.aws.cognito_auth import CognitoAuthService

security = HTTPBearer()


async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    cognito_service: CognitoAuthService = Depends(),
) -> dict[str, Any]:
    """
    Verify JWT token from Cognito.

    Args:
        credentials: Authorization credentials with Bearer token
        cognito_service: Cognito authentication service

    Returns:
        Decoded token claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        token = credentials.credentials
        claims = await cognito_service.verify_token(token)
        return claims

    except ValueError as e:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User ID not found in token claims",
        )
    return user_id
