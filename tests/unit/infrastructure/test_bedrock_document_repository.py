"""Unit tests for BedrockDocumentRepository."""
from unittest.mock import AsyncMock, Mock, patch

import pytest

from src.domain.entities.document import Document, DocumentChunk
from src.infrastructure.repositories.bedrock_document_repository import (
    BedrockDocumentRepository,
)


@pytest.mark.unit
class TestBedrockDocumentRepository:
    """Unit tests for BedrockDocumentRepository."""

    @pytest.fixture
    def mock_bedrock_client(self):
        """Create mock Bedrock client."""
        mock = Mock()
        mock.retrieve_and_generate = Mock()
        return mock

    @pytest.fixture
    def repository(self, mock_bedrock_client):
        """Create repository with mocked Bedrock client."""
        with patch("boto3.client", return_value=mock_bedrock_client):
            repo = BedrockDocumentRepository(
                knowledge_base_id="kb-123",
                model_arn="arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-sonnet-20240229-v1:0",
                region="us-east-1",
            )
            repo._bedrock_agent = mock_bedrock_client
            return repo

    @pytest.mark.asyncio
    async def test_search_documents_returns_documents(self, repository, mock_bedrock_client):
        """Test that search_documents returns list of Documents."""
        # Arrange
        mock_bedrock_client.retrieve_and_generate.return_value = {
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {"text": "Amazon revenue grew 15%"},
                            "location": {"s3Location": {"uri": "s3://bucket/doc1.pdf"}},
                            "metadata": {"source": "Annual Report 2024"},
                        }
                    ]
                }
            ],
            "output": {"text": "Amazon revenue information..."},
        }

        # Act
        results = await repository.search_documents("revenue growth", max_results=5)

        # Assert
        assert len(results) == 1
        assert isinstance(results[0], Document)
        assert results[0].content == "Amazon revenue grew 15%"
        assert "s3://bucket/doc1.pdf" in results[0].source
        mock_bedrock_client.retrieve_and_generate.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_documents_with_no_results(self, repository, mock_bedrock_client):
        """Test search_documents returns empty list when no results."""
        # Arrange
        mock_bedrock_client.retrieve_and_generate.return_value = {
            "citations": [],
            "output": {"text": "No relevant information found."},
        }

        # Act
        results = await repository.search_documents("nonexistent query")

        # Assert
        assert results == []

    @pytest.mark.asyncio
    async def test_search_documents_calls_bedrock_with_correct_params(
        self, repository, mock_bedrock_client
    ):
        """Test that Bedrock is called with correct parameters."""
        # Arrange
        mock_bedrock_client.retrieve_and_generate.return_value = {
            "citations": [],
            "output": {"text": ""},
        }

        # Act
        await repository.search_documents("test query", max_results=10)

        # Assert
        call_args = mock_bedrock_client.retrieve_and_generate.call_args[1]
        assert call_args["input"]["text"] == "test query"
        assert call_args["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"][
            "knowledgeBaseId"
        ] == "kb-123"
        assert call_args["retrieveAndGenerateConfiguration"]["knowledgeBaseConfiguration"][
            "retrievalConfiguration"
        ]["vectorSearchConfiguration"]["numberOfResults"] == 10

    @pytest.mark.asyncio
    async def test_search_documents_handles_missing_metadata(
        self, repository, mock_bedrock_client
    ):
        """Test that search handles missing metadata gracefully."""
        # Arrange
        mock_bedrock_client.retrieve_and_generate.return_value = {
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {"text": "Some content"},
                            "location": {"s3Location": {"uri": "s3://bucket/doc.pdf"}},
                            # No metadata field
                        }
                    ]
                }
            ],
            "output": {"text": "Result"},
        }

        # Act
        results = await repository.search_documents("query")

        # Assert
        assert len(results) == 1
        assert results[0].metadata == {}

    @pytest.mark.asyncio
    async def test_search_documents_raises_runtime_error_on_bedrock_failure(
        self, repository, mock_bedrock_client
    ):
        """Test that RuntimeError is raised when Bedrock fails."""
        # Arrange
        mock_bedrock_client.retrieve_and_generate.side_effect = Exception(
            "Bedrock API error"
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="Failed to search documents"):
            await repository.search_documents("query")

    @pytest.mark.asyncio
    async def test_search_documents_validates_query_not_empty(self, repository):
        """Test that empty query raises ValueError."""
        # Act & Assert
        with pytest.raises(ValueError, match="cannot be empty"):
            await repository.search_documents("")

    @pytest.mark.asyncio
    async def test_search_documents_validates_max_results_positive(self, repository):
        """Test that max_results must be positive."""
        # Act & Assert
        with pytest.raises(ValueError, match="must be positive"):
            await repository.search_documents("query", max_results=0)

        with pytest.raises(ValueError, match="must be positive"):
            await repository.search_documents("query", max_results=-1)

    @pytest.mark.asyncio
    async def test_search_documents_extracts_chunks_when_present(
        self, repository, mock_bedrock_client
    ):
        """Test that DocumentChunks are extracted from citations."""
        # Arrange
        mock_bedrock_client.retrieve_and_generate.return_value = {
            "citations": [
                {
                    "retrievedReferences": [
                        {
                            "content": {"text": "Chunk 1"},
                            "location": {"s3Location": {"uri": "s3://bucket/doc.pdf"}},
                            "metadata": {"page": "5"},
                        },
                        {
                            "content": {"text": "Chunk 2"},
                            "location": {"s3Location": {"uri": "s3://bucket/doc.pdf"}},
                            "metadata": {"page": "6"},
                        },
                    ]
                }
            ],
            "output": {"text": "Result"},
        }

        # Act
        results = await repository.search_documents("query")

        # Assert
        assert len(results) == 2
        assert results[0].content == "Chunk 1"
        assert results[1].content == "Chunk 2"
