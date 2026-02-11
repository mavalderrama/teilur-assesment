"""Unit tests for QueryDocumentsUseCase."""
from unittest.mock import AsyncMock, Mock

import pytest

from src.application.use_cases.query_documents import QueryDocumentsUseCase
from src.domain.entities.document import DocumentChunk
from src.domain.interfaces.document_repository import IDocumentRepository


@pytest.fixture
def mock_document_repository():
    """Create a mock document repository."""
    return Mock(spec=IDocumentRepository)


@pytest.fixture
def use_case(mock_document_repository):
    """Create use case with mocked repository."""
    return QueryDocumentsUseCase(document_repository=mock_document_repository)


class TestQueryDocumentsUseCase:
    """Tests for QueryDocumentsUseCase."""

    @pytest.mark.asyncio
    async def test_execute_with_valid_query(self, use_case, mock_document_repository):
        """Test executing use case with valid query."""
        # Arrange
        expected_chunks = [
            DocumentChunk(
                document_id="doc_1",
                chunk_id="chunk_1",
                content="Amazon's AI strategy...",
                relevance_score=0.95,
            ),
            DocumentChunk(
                document_id="doc_2",
                chunk_id="chunk_2",
                content="Investment in generative AI...",
                relevance_score=0.88,
            ),
        ]
        mock_document_repository.search_documents = AsyncMock(return_value=expected_chunks)

        # Act
        result = await use_case.execute("What is Amazon's AI strategy?", max_results=5)

        # Assert
        assert result == expected_chunks
        mock_document_repository.search_documents.assert_called_once_with(
            "What is Amazon's AI strategy?", 5
        )

    @pytest.mark.asyncio
    async def test_execute_strips_whitespace(self, use_case, mock_document_repository):
        """Test that query whitespace is stripped."""
        # Arrange
        mock_document_repository.search_documents = AsyncMock(return_value=[])

        # Act
        await use_case.execute("  test query  ")

        # Assert
        mock_document_repository.search_documents.assert_called_once_with("test query", 5)

    @pytest.mark.asyncio
    async def test_execute_with_empty_query_raises_error(self, use_case):
        """Test that empty query raises ValueError."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            await use_case.execute("")

    @pytest.mark.asyncio
    async def test_execute_with_none_query_raises_error(self, use_case):
        """Test that None query raises ValueError."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            await use_case.execute(None)  # type: ignore

    @pytest.mark.asyncio
    async def test_execute_with_non_string_query_raises_error(self, use_case):
        """Test that non-string query raises ValueError."""
        with pytest.raises(ValueError, match="Query must be a non-empty string"):
            await use_case.execute(123)  # type: ignore

    @pytest.mark.asyncio
    async def test_execute_with_whitespace_only_query_raises_error(self, use_case):
        """Test that whitespace-only query raises ValueError."""
        with pytest.raises(ValueError, match="Query cannot be empty after normalization"):
            await use_case.execute("   ")

    @pytest.mark.asyncio
    async def test_execute_with_invalid_max_results_raises_error(self, use_case):
        """Test that invalid max_results raises ValueError."""
        # Non-integer
        with pytest.raises(ValueError, match="Max results must be a positive integer"):
            await use_case.execute("test query", max_results="5")  # type: ignore

        # Zero
        with pytest.raises(ValueError, match="Max results must be a positive integer"):
            await use_case.execute("test query", max_results=0)

        # Negative
        with pytest.raises(ValueError, match="Max results must be a positive integer"):
            await use_case.execute("test query", max_results=-1)

    @pytest.mark.asyncio
    async def test_execute_with_custom_max_results(self, use_case, mock_document_repository):
        """Test that custom max_results is passed to repository."""
        # Arrange
        mock_document_repository.search_documents = AsyncMock(return_value=[])

        # Act
        await use_case.execute("test query", max_results=10)

        # Assert
        mock_document_repository.search_documents.assert_called_once_with("test query", 10)

    @pytest.mark.asyncio
    async def test_execute_returns_empty_list_when_no_results(
        self, use_case, mock_document_repository
    ):
        """Test that empty list is returned when no documents found."""
        # Arrange
        mock_document_repository.search_documents = AsyncMock(return_value=[])

        # Act
        result = await use_case.execute("query with no results")

        # Assert
        assert result == []

    @pytest.mark.asyncio
    async def test_execute_propagates_repository_errors(
        self, use_case, mock_document_repository
    ):
        """Test that repository errors are propagated."""
        # Arrange
        mock_document_repository.search_documents = AsyncMock(
            side_effect=RuntimeError("Search service unavailable")
        )

        # Act & Assert
        with pytest.raises(RuntimeError, match="Search service unavailable"):
            await use_case.execute("test query")
