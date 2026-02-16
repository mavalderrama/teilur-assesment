"""API routes for authentication."""
from fastapi import APIRouter, Depends, HTTPException

from src.di.container import get_cognito_service
from src.presentation.api.schemas.request import AuthRequest
from src.presentation.api.schemas.response import AuthResponse, ErrorResponse

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        200: {"description": "Successful authentication"},
        400: {"model": ErrorResponse, "description": "Invalid credentials"},
        401: {"model": ErrorResponse, "description": "Authentication failed"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
)
async def login(
    request: AuthRequest,
    cognito_service=Depends(get_cognito_service),
) -> AuthResponse:
    """
    Authenticate a user with username and password.

    Returns JWT tokens (access, ID, and refresh) for authenticated requests.
    """
    try:
        tokens = await cognito_service.authenticate_user(request.username, request.password)

        return AuthResponse(
            access_token=tokens["access_token"],
            id_token=tokens["id_token"],
            refresh_token=tokens["refresh_token"],
            token_type="Bearer",
            expires_in=3600,  # 1 hour
        )

    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
