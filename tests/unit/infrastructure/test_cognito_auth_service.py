"""Unit tests for CognitoAuthService."""
from unittest.mock import Mock, patch

import pytest

from src.infrastructure.auth.cognito_auth_service import CognitoAuthService


@pytest.mark.unit
class TestCognitoAuthService:
    """Unit tests for CognitoAuthService."""

    @pytest.fixture
    def mock_cognito_client(self):
        """Create mock Cognito client."""
        mock = Mock()
        mock.initiate_auth = Mock()
        return mock

    @pytest.fixture
    def auth_service(self, mock_cognito_client):
        """Create auth service with mocked Cognito client."""
        with patch("boto3.client", return_value=mock_cognito_client):
            service = CognitoAuthService(
                user_pool_id="us-east-1_ABC123",
                client_id="client123",
                region="us-east-1",
            )
            service._cognito = mock_cognito_client
            return service

    def test_authenticate_returns_token_on_success(self, auth_service, mock_cognito_client):
        """Test that authenticate returns token on successful authentication."""
        # Arrange
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "AccessToken": "access_token_123",
                "RefreshToken": "refresh_token_123",
                "ExpiresIn": 3600,
            }
        }

        # Act
        result = auth_service.authenticate("testuser", "password123")

        # Assert
        assert result["id_token"] == "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        assert result["access_token"] == "access_token_123"
        assert result["refresh_token"] == "refresh_token_123"
        assert result["expires_in"] == 3600

    def test_authenticate_calls_cognito_with_correct_params(
        self, auth_service, mock_cognito_client
    ):
        """Test that Cognito is called with correct parameters."""
        # Arrange
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "token",
                "AccessToken": "access",
                "RefreshToken": "refresh",
                "ExpiresIn": 3600,
            }
        }

        # Act
        auth_service.authenticate("testuser", "password123")

        # Assert
        mock_cognito_client.initiate_auth.assert_called_once_with(
            ClientId="client123",
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={
                "USERNAME": "testuser",
                "PASSWORD": "password123",
            },
        )

    def test_authenticate_raises_value_error_on_empty_username(self, auth_service):
        """Test that authenticate raises ValueError for empty username."""
        # Act & Assert
        with pytest.raises(ValueError, match="Username cannot be empty"):
            auth_service.authenticate("", "password123")

    def test_authenticate_raises_value_error_on_empty_password(self, auth_service):
        """Test that authenticate raises ValueError for empty password."""
        # Act & Assert
        with pytest.raises(ValueError, match="Password cannot be empty"):
            auth_service.authenticate("testuser", "")

    def test_authenticate_raises_runtime_error_on_invalid_credentials(
        self, auth_service, mock_cognito_client
    ):
        """Test that authenticate raises RuntimeError on invalid credentials."""
        # Arrange
        mock_cognito_client.initiate_auth.side_effect = Exception("NotAuthorizedException")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Authentication failed"):
            auth_service.authenticate("testuser", "wrongpassword")

    def test_authenticate_raises_runtime_error_on_cognito_failure(
        self, auth_service, mock_cognito_client
    ):
        """Test that authenticate raises RuntimeError on Cognito service failure."""
        # Arrange
        mock_cognito_client.initiate_auth.side_effect = Exception("Service unavailable")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Authentication failed"):
            auth_service.authenticate("testuser", "password123")

    def test_verify_token_returns_claims_on_valid_token(self, auth_service):
        """Test that verify_token returns decoded claims for valid token."""
        # Note: This would require mocking JWT verification
        # For now, test the structure
        with patch("jwt.decode") as mock_decode:
            mock_decode.return_value = {
                "sub": "user-123",
                "email": "test@example.com",
                "cognito:username": "testuser",
            }

            # Act
            claims = auth_service.verify_token("valid.jwt.token")

            # Assert
            assert claims["sub"] == "user-123"
            assert claims["email"] == "test@example.com"
            assert claims["cognito:username"] == "testuser"

    def test_verify_token_raises_runtime_error_on_invalid_token(self, auth_service):
        """Test that verify_token raises RuntimeError for invalid token."""
        # Arrange
        with patch("jwt.decode", side_effect=Exception("Invalid signature")):
            # Act & Assert
            with pytest.raises(RuntimeError, match="Token verification failed"):
                auth_service.verify_token("invalid.jwt.token")

    def test_verify_token_raises_value_error_on_empty_token(self, auth_service):
        """Test that verify_token raises ValueError for empty token."""
        # Act & Assert
        with pytest.raises(ValueError, match="Token cannot be empty"):
            auth_service.verify_token("")

    def test_refresh_token_returns_new_token_on_success(
        self, auth_service, mock_cognito_client
    ):
        """Test that refresh_token returns new tokens."""
        # Arrange
        mock_cognito_client.initiate_auth.return_value = {
            "AuthenticationResult": {
                "IdToken": "new.id.token",
                "AccessToken": "new_access_token",
                "ExpiresIn": 3600,
            }
        }

        # Act
        result = auth_service.refresh_token("refresh_token_123")

        # Assert
        assert result["id_token"] == "new.id.token"
        assert result["access_token"] == "new_access_token"
        assert result["expires_in"] == 3600
        mock_cognito_client.initiate_auth.assert_called_once_with(
            ClientId="client123",
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={
                "REFRESH_TOKEN": "refresh_token_123",
            },
        )

    def test_refresh_token_raises_value_error_on_empty_token(self, auth_service):
        """Test that refresh_token raises ValueError for empty token."""
        # Act & Assert
        with pytest.raises(ValueError, match="Refresh token cannot be empty"):
            auth_service.refresh_token("")

    def test_refresh_token_raises_runtime_error_on_failure(
        self, auth_service, mock_cognito_client
    ):
        """Test that refresh_token raises RuntimeError on failure."""
        # Arrange
        mock_cognito_client.initiate_auth.side_effect = Exception("Invalid refresh token")

        # Act & Assert
        with pytest.raises(RuntimeError, match="Token refresh failed"):
            auth_service.refresh_token("invalid_refresh_token")
