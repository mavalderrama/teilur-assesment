"""Unit tests for DIContainer."""
import os
from unittest.mock import Mock, patch

import pytest

from src.di.container import DIContainer


@pytest.mark.unit
class TestDIContainer:
    """Unit tests for DIContainer."""

    @pytest.fixture
    def clean_env(self):
        """Fixture to clean environment variables before and after test."""
        original_env = os.environ.copy()
        # Clear relevant env vars
        for key in list(os.environ.keys()):
            if key.startswith(("AWS_", "BEDROCK_", "COGNITO_", "LANGFUSE_", "LANGSMITH_", "OBSERVABILITY_")):
                del os.environ[key]
        yield
        # Restore original environment
        os.environ.clear()
        os.environ.update(original_env)

    def test_container_initializes_with_environment_variables(self, clean_env):
        """Test that container reads configuration from environment."""
        # Arrange
        os.environ["AWS_REGION"] = "us-west-2"
        os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"
        os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = "kb-test-123"

        # Act
        container = DIContainer()

        # Assert
        assert container.aws_region == "us-west-2"
        assert container.bedrock_model_id == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert container.bedrock_kb_id == "kb-test-123"

    def test_container_uses_default_values_when_env_not_set(self, clean_env):
        """Test that container uses defaults when env vars not set."""
        # Act
        container = DIContainer()

        # Assert
        assert container.aws_region == "us-east-1"  # Default
        assert container.observability_provider == "none"  # Default

    def test_stock_repository_returns_yfinance_repository(self, clean_env):
        """Test that stock_repository returns YFinanceStockRepository."""
        # Arrange
        container = DIContainer()

        # Act
        repo = container.stock_repository

        # Assert
        from src.infrastructure.repositories.yfinance_stock_repository import (
            YFinanceStockRepository,
        )
        assert isinstance(repo, YFinanceStockRepository)

    def test_stock_repository_is_singleton(self, clean_env):
        """Test that stock_repository returns same instance on multiple calls."""
        # Arrange
        container = DIContainer()

        # Act
        repo1 = container.stock_repository
        repo2 = container.stock_repository

        # Assert
        assert repo1 is repo2

    @patch("boto3.client")
    def test_document_repository_returns_bedrock_repository(self, mock_boto_client, clean_env):
        """Test that document_repository returns BedrockDocumentRepository."""
        # Arrange
        os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = "kb-123"
        os.environ["BEDROCK_MODEL_ARN"] = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        container = DIContainer()

        # Act
        repo = container.document_repository

        # Assert
        from src.infrastructure.repositories.bedrock_document_repository import (
            BedrockDocumentRepository,
        )
        assert isinstance(repo, BedrockDocumentRepository)

    def test_observability_service_returns_none_when_provider_is_none(self, clean_env):
        """Test that observability_service returns None when provider is 'none'."""
        # Arrange
        os.environ["OBSERVABILITY_PROVIDER"] = "none"
        container = DIContainer()

        # Act
        service = container.observability_service

        # Assert
        assert service is None

    def test_observability_service_returns_langfuse_when_configured(self, clean_env):
        """Test that observability_service returns LangfuseObservabilityService."""
        # Arrange
        os.environ["OBSERVABILITY_PROVIDER"] = "langfuse"
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test"
        os.environ["LANGFUSE_HOST"] = "https://cloud.langfuse.com"

        with patch("src.infrastructure.services.langfuse_observability.Langfuse"):
            container = DIContainer()

            # Act
            service = container.observability_service

            # Assert
            from src.infrastructure.services.langfuse_observability import (
                LangfuseObservabilityService,
            )
            assert isinstance(service, LangfuseObservabilityService)

    def test_observability_service_returns_langsmith_when_configured(self, clean_env):
        """Test that observability_service returns LangSmithObservabilityService."""
        # Arrange
        os.environ["OBSERVABILITY_PROVIDER"] = "langsmith"
        os.environ["LANGSMITH_API_KEY"] = "lsv2_pt_test"
        os.environ["LANGSMITH_PROJECT"] = "test-project"

        with patch("src.infrastructure.services.langsmith_observability.Client"):
            container = DIContainer()

            # Act
            service = container.observability_service

            # Assert
            from src.infrastructure.services.langsmith_observability import (
                LangSmithObservabilityService,
            )
            assert isinstance(service, LangSmithObservabilityService)

    def test_observability_service_is_singleton(self, clean_env):
        """Test that observability_service returns same instance."""
        # Arrange
        os.environ["OBSERVABILITY_PROVIDER"] = "langfuse"
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk-lf-test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk-lf-test"

        with patch("src.infrastructure.services.langfuse_observability.Langfuse"):
            container = DIContainer()

            # Act
            service1 = container.observability_service
            service2 = container.observability_service

            # Assert
            assert service1 is service2

    def test_get_realtime_stock_price_use_case_returns_use_case(self, clean_env):
        """Test that get_realtime_stock_price_uc returns use case with injected repository."""
        # Arrange
        container = DIContainer()

        # Act
        use_case = container.get_realtime_stock_price_uc

        # Assert
        from src.application.use_cases.get_realtime_stock_price import (
            GetRealtimeStockPriceUseCase,
        )
        assert isinstance(use_case, GetRealtimeStockPriceUseCase)

    def test_get_historical_stock_price_use_case_returns_use_case(self, clean_env):
        """Test that get_historical_stock_price_uc returns use case with injected repository."""
        # Arrange
        container = DIContainer()

        # Act
        use_case = container.get_historical_stock_price_uc

        # Assert
        from src.application.use_cases.get_historical_stock_price import (
            GetHistoricalStockPriceUseCase,
        )
        assert isinstance(use_case, GetHistoricalStockPriceUseCase)

    @patch("boto3.client")
    def test_query_documents_use_case_returns_use_case(self, mock_boto_client, clean_env):
        """Test that query_documents_uc returns use case with injected repository."""
        # Arrange
        os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = "kb-123"
        os.environ["BEDROCK_MODEL_ARN"] = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
        container = DIContainer()

        # Act
        use_case = container.query_documents_uc

        # Assert
        from src.application.use_cases.query_documents import QueryDocumentsUseCase
        assert isinstance(use_case, QueryDocumentsUseCase)

    def test_agent_tools_returns_agent_tools_with_use_cases(self, clean_env):
        """Test that agent_tools returns AgentTools with all use cases injected."""
        # Arrange
        with patch("boto3.client"):
            os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = "kb-123"
            os.environ["BEDROCK_MODEL_ARN"] = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            container = DIContainer()

            # Act
            tools = container.agent_tools

            # Assert
            from src.infrastructure.agent.tools import AgentTools
            assert isinstance(tools, AgentTools)

    @patch("boto3.client")
    def test_orchestrator_returns_langgraph_orchestrator(self, mock_boto_client, clean_env):
        """Test that orchestrator returns LangGraphOrchestrator."""
        # Arrange
        os.environ["BEDROCK_MODEL_ID"] = "anthropic.claude-3-sonnet-20240229-v1:0"
        os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = "kb-123"
        os.environ["BEDROCK_MODEL_ARN"] = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"

        with patch("src.infrastructure.agent.langgraph_orchestrator.ChatBedrock"):
            container = DIContainer()

            # Act
            orchestrator = container.orchestrator

            # Assert
            from src.infrastructure.agent.langgraph_orchestrator import (
                LangGraphOrchestrator,
            )
            assert isinstance(orchestrator, LangGraphOrchestrator)

    def test_orchestrator_is_singleton(self, clean_env):
        """Test that orchestrator returns same instance."""
        # Arrange
        with patch("boto3.client"), patch(
            "src.infrastructure.agent.langgraph_orchestrator.ChatBedrock"
        ):
            os.environ["BEDROCK_KNOWLEDGE_BASE_ID"] = "kb-123"
            os.environ["BEDROCK_MODEL_ARN"] = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0"
            container = DIContainer()

            # Act
            orch1 = container.orchestrator
            orch2 = container.orchestrator

            # Assert
            assert orch1 is orch2

    @patch("boto3.client")
    def test_auth_service_returns_cognito_auth_service(self, mock_boto_client, clean_env):
        """Test that auth_service returns CognitoAuthService."""
        # Arrange
        os.environ["COGNITO_USER_POOL_ID"] = "us-east-1_ABC123"
        os.environ["COGNITO_CLIENT_ID"] = "client123"
        container = DIContainer()

        # Act
        service = container.auth_service

        # Assert
        from src.infrastructure.auth.cognito_auth_service import CognitoAuthService
        assert isinstance(service, CognitoAuthService)

    def test_missing_required_env_vars_handled_gracefully(self, clean_env):
        """Test that container handles missing env vars gracefully."""
        # Act - No environment variables set
        container = DIContainer()

        # Assert - Should still initialize with defaults
        assert container.aws_region == "us-east-1"
        assert container.observability_provider == "none"
