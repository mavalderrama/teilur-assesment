"""Dependency Injection Container for Clean Architecture."""
import os
from functools import lru_cache

from src.application.interfaces.agent_orchestrator import IAgentOrchestrator
from src.application.use_cases.get_historical_stock_price import (
    GetHistoricalStockPriceUseCase,
)
from src.application.use_cases.get_realtime_stock_price import (
    GetRealtimeStockPriceUseCase,
)
from src.application.use_cases.query_documents import QueryDocumentsUseCase
from src.domain.interfaces.document_repository import IDocumentRepository
from src.domain.interfaces.observability_service import IObservabilityService
from src.domain.interfaces.stock_repository import IStockRepository
from src.infrastructure.agent.langgraph_orchestrator import LangGraphOrchestrator
from src.infrastructure.agent.tools import AgentTools
from src.infrastructure.aws.cognito_auth import CognitoAuthService
from src.infrastructure.repositories.bedrock_document_repository import (
    BedrockDocumentRepository,
)
from src.infrastructure.repositories.yfinance_stock_repository import (
    YFinanceStockRepository,
)
from src.infrastructure.services.langfuse_observability import (
    LangfuseObservabilityService,
)
from src.infrastructure.services.langsmith_observability import (
    LangSmithObservabilityService,
)


class DIContainer:
    """Dependency Injection Container - wires all layers together."""

    def __init__(self) -> None:
        """Initialize container with environment configuration."""
        # AWS Configuration
        self.aws_region = os.getenv("AWS_REGION", "us-east-1")
        self.bedrock_model_id = os.getenv(
            "BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0"
        )
        self.bedrock_knowledge_base_id = os.getenv("BEDROCK_KNOWLEDGE_BASE_ID", "")

        # Cognito Configuration
        self.cognito_user_pool_id = os.getenv("COGNITO_USER_POOL_ID", "")
        self.cognito_app_client_id = os.getenv("COGNITO_APP_CLIENT_ID", "")

        # Observability Configuration
        self.observability_provider = os.getenv("OBSERVABILITY_PROVIDER", "langfuse")  # langfuse or langsmith

        # Langfuse Configuration
        self.langfuse_public_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        self.langfuse_secret_key = os.getenv("LANGFUSE_SECRET_KEY", "")
        self.langfuse_host = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")

        # LangSmith Configuration
        self.langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT", "aws-ai-agent")
        self.langsmith_endpoint = os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com")

        # Initialize singletons
        self._stock_repository: IStockRepository | None = None
        self._document_repository: IDocumentRepository | None = None
        self._observability_service: IObservabilityService | None = None
        self._cognito_service: CognitoAuthService | None = None
        self._agent_orchestrator: IAgentOrchestrator | None = None

    # Repositories
    @property
    def stock_repository(self) -> IStockRepository:
        """Get stock repository instance."""
        if self._stock_repository is None:
            self._stock_repository = YFinanceStockRepository()
        return self._stock_repository

    @property
    def document_repository(self) -> IDocumentRepository:
        """Get document repository instance."""
        if self._document_repository is None:
            if not self.bedrock_knowledge_base_id:
                raise ValueError("BEDROCK_KNOWLEDGE_BASE_ID environment variable not set")
            self._document_repository = BedrockDocumentRepository(
                knowledge_base_id=self.bedrock_knowledge_base_id,
                region=self.aws_region,
            )
        return self._document_repository

    # Services
    @property
    def observability_service(self) -> IObservabilityService | None:
        """
        Get observability service instance based on configuration.

        Returns Langfuse or LangSmith service based on OBSERVABILITY_PROVIDER env var.
        Returns None if observability is not configured.
        """
        if self._observability_service is None:
            if self.observability_provider == "langsmith":
                # Use LangSmith
                if self.langsmith_api_key:
                    self._observability_service = LangSmithObservabilityService(
                        api_key=self.langsmith_api_key,
                        project_name=self.langsmith_project,
                        endpoint=self.langsmith_endpoint,
                    )
            elif self.observability_provider == "langfuse":
                # Use Langfuse (default)
                if self.langfuse_public_key and self.langfuse_secret_key:
                    self._observability_service = LangfuseObservabilityService(
                        public_key=self.langfuse_public_key,
                        secret_key=self.langfuse_secret_key,
                        host=self.langfuse_host,
                    )
            # Return None if not configured (observability is optional)
        return self._observability_service

    @property
    def cognito_service(self) -> CognitoAuthService:
        """Get Cognito authentication service instance."""
        if self._cognito_service is None:
            if not self.cognito_user_pool_id or not self.cognito_app_client_id:
                raise ValueError("Cognito environment variables not set")
            self._cognito_service = CognitoAuthService(
                user_pool_id=self.cognito_user_pool_id,
                app_client_id=self.cognito_app_client_id,
                region=self.aws_region,
            )
        return self._cognito_service

    # Use Cases
    def get_realtime_stock_price_use_case(self) -> GetRealtimeStockPriceUseCase:
        """Get realtime stock price use case."""
        return GetRealtimeStockPriceUseCase(stock_repository=self.stock_repository)

    def get_historical_stock_price_use_case(self) -> GetHistoricalStockPriceUseCase:
        """Get historical stock price use case."""
        return GetHistoricalStockPriceUseCase(stock_repository=self.stock_repository)

    def query_documents_use_case(self) -> QueryDocumentsUseCase:
        """Get query documents use case."""
        return QueryDocumentsUseCase(document_repository=self.document_repository)

    # Agent
    def create_agent_tools(self) -> AgentTools:
        """Create agent tools with use cases."""
        return AgentTools(
            get_realtime_price_uc=self.get_realtime_stock_price_use_case(),
            get_historical_price_uc=self.get_historical_stock_price_use_case(),
            query_documents_uc=self.query_documents_use_case(),
        )

    @property
    def agent_orchestrator(self) -> IAgentOrchestrator:
        """Get agent orchestrator instance."""
        if self._agent_orchestrator is None:
            self._agent_orchestrator = LangGraphOrchestrator(
                llm_model_id=self.bedrock_model_id,
                region=self.aws_region,
                agent_tools=self.create_agent_tools(),
                observability_service=self.observability_service,
            )
        return self._agent_orchestrator


# FastAPI dependency providers
@lru_cache
def get_container() -> DIContainer:
    """Get DI container singleton."""
    return DIContainer()


def get_cognito_service() -> CognitoAuthService:
    """FastAPI dependency for Cognito service."""
    return get_container().cognito_service


def get_agent_orchestrator() -> IAgentOrchestrator:
    """FastAPI dependency for agent orchestrator."""
    return get_container().agent_orchestrator
