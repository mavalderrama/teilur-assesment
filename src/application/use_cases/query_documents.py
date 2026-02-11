"""Use case for querying documents with semantic search."""
from src.domain.entities.document import DocumentChunk
from src.domain.interfaces.document_repository import IDocumentRepository


class QueryDocumentsUseCase:
    """Use case for querying documents."""

    def __init__(self, document_repository: IDocumentRepository) -> None:
        """
        Initialize use case with dependencies.

        Args:
            document_repository: Document repository implementation
        """
        self._document_repository = document_repository

    async def execute(self, query: str, max_results: int = 5) -> list[DocumentChunk]:
        """
        Execute use case to query documents.

        Args:
            query: Search query text
            max_results: Maximum number of results to return

        Returns:
            List of relevant document chunks ranked by relevance

        Raises:
            ValueError: If query is invalid
            RuntimeError: If search operation fails
        """
        # Validate inputs
        if not query or not isinstance(query, str):
            raise ValueError("Query must be a non-empty string")

        if not isinstance(max_results, int) or max_results < 1:
            raise ValueError("Max results must be a positive integer")

        # Normalize query
        normalized_query = query.strip()

        if not normalized_query:
            raise ValueError("Query cannot be empty after normalization")

        # Delegate to repository
        return await self._document_repository.search_documents(normalized_query, max_results)
