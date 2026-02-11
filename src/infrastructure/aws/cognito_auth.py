"""AWS Cognito authentication service."""
import boto3
from botocore.config import Config
from jose import JWTError, jwt
from jose.backends import RSAKey


class CognitoAuthService:
    """Service for AWS Cognito authentication and token validation."""

    def __init__(
        self,
        user_pool_id: str,
        app_client_id: str,
        region: str = "us-east-1",
    ) -> None:
        """
        Initialize Cognito auth service.

        Args:
            user_pool_id: Cognito user pool ID
            app_client_id: Cognito app client ID
            region: AWS region
        """
        self._user_pool_id = user_pool_id
        self._app_client_id = app_client_id
        self._region = region
        self._issuer = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"

        config = Config(region_name=region)
        self._cognito_client = boto3.client("cognito-idp", config=config)

        # Cache for JWKS (JSON Web Key Set)
        self._jwks: dict[str, Any] | None = None

    def _get_jwks(self) -> dict[str, Any]:
        """Fetch and cache JSON Web Key Set from Cognito."""
        if self._jwks is None:
            import requests

            jwks_url = f"{self._issuer}/.well-known/jwks.json"
            response = requests.get(jwks_url, timeout=10)
            response.raise_for_status()
            self._jwks = response.json()

        return self._jwks

    async def verify_token(self, token: str) -> dict[str, Any]:
        """
        Verify a Cognito JWT token.

        Args:
            token: JWT access token from Cognito

        Returns:
            Decoded token claims

        Raises:
            ValueError: If token is invalid or expired
        """
        try:
            # Get the key ID from token headers
            headers = jwt.get_unverified_headers(token)
            kid = headers.get("kid")

            if not kid:
                raise ValueError("Token missing key ID")

            # Find the matching key from JWKS
            jwks = self._get_jwks()
            key = None
            for jwk in jwks.get("keys", []):
                if jwk.get("kid") == kid:
                    key = jwk
                    break

            if not key:
                raise ValueError("Public key not found in JWKS")

            # Verify and decode token
            claims = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self._app_client_id,
                issuer=self._issuer,
            )

            return claims

        except JWTError as e:
            raise ValueError(f"Invalid token: {str(e)}")

    async def authenticate_user(self, username: str, password: str) -> dict[str, str]:
        """
        Authenticate a user with username and password.

        Args:
            username: Cognito username
            password: User password

        Returns:
            Dictionary with access_token, id_token, refresh_token

        Raises:
            ValueError: If authentication fails
        """
        try:
            response = self._cognito_client.initiate_auth(
                ClientId=self._app_client_id,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": username, "PASSWORD": password},
            )

            auth_result = response.get("AuthenticationResult")
            if not auth_result:
                raise ValueError("Authentication failed")

            return {
                "access_token": auth_result.get("AccessToken", ""),
                "id_token": auth_result.get("IdToken", ""),
                "refresh_token": auth_result.get("RefreshToken", ""),
            }

        except Exception as e:
            raise ValueError(f"Authentication failed: {str(e)}")

    async def create_user(
        self, username: str, password: str, email: str, temp_password: bool = False
    ) -> str:
        """
        Create a new user in Cognito.

        Args:
            username: Desired username
            password: User password
            email: User email address
            temp_password: Whether password is temporary

        Returns:
            User sub (unique identifier)

        Raises:
            RuntimeError: If user creation fails
        """
        try:
            response = self._cognito_client.admin_create_user(
                UserPoolId=self._user_pool_id,
                Username=username,
                UserAttributes=[{"Name": "email", "Value": email}],
                TemporaryPassword=password if temp_password else None,
                MessageAction="SUPPRESS",  # Don't send welcome email
            )

            if not temp_password:
                # Set permanent password
                self._cognito_client.admin_set_user_password(
                    UserPoolId=self._user_pool_id,
                    Username=username,
                    Password=password,
                    Permanent=True,
                )

            user = response.get("User", {})
            for attr in user.get("Attributes", []):
                if attr["Name"] == "sub":
                    return attr["Value"]

            raise RuntimeError("User sub not found in response")

        except Exception as e:
            raise RuntimeError(f"Failed to create user: {str(e)}")
