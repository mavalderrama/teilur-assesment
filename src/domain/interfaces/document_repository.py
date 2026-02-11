"""Document repository interface - defines contract for document access."""
from abc import ABC, abstractmethod

from src.domain.entities.document import Document, DocumentChunk


class IDocumentRepository(ABC):
    """Interface for document repository."""

    @abstractmethod
    async def search_documents(self, query: str, max_results: int = 5) -> list[DocumentChunk]:
        """
        Search documents using semantic search.

        Args:
            query: Search query text
            max_results: Maximum number of results to return

        Returns:
            List of relevant document chunks ranked by relevance

        Raises:
            RuntimeError: If search operation fails
        """
        pass

    @abstractmethod
    async def get_document_by_id(self, document_id: str) -> Document:
        """
        Retrieve a document by its ID.

        Args:
            document_id: Unique document identifier

        Returns:
            Document entity

        Raises:
            ValueError: If document_id is invalid
            RuntimeError: If document cannot be retrieved
        """
        pass

    @abstractmethod
    async def list_documents(self, company: str) -> list[Document]:
        """
        List all documents for a company.

        Args:
            company: Company name to filter documents

        Returns:
            List of documents for the specified company

        Raises:
            RuntimeError: If listing operation fails
        """
        pass
