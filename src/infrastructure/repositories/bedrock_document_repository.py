"""Bedrock document repository implementation."""
from typing import Any

import boto3
from botocore.config import Config

from src.domain.entities.document import Document, DocumentChunk
from src.domain.interfaces.document_repository import IDocumentRepository
from src.infrastructure.logging import get_logger

logger = get_logger(__name__)


class BedrockDocumentRepository(IDocumentRepository):
    """Repository implementation using AWS Bedrock Knowledge Base."""

    def __init__(
        self,
        knowledge_base_id: str,
        region: str = "us-east-1",
        boto_config: Config | None = None,
    ) -> None:
        """
        Initialize repository with Bedrock configuration.

        Args:
            knowledge_base_id: AWS Bedrock Knowledge Base ID
            region: AWS region
            boto_config: Optional boto3 configuration
        """
        self._knowledge_base_id = knowledge_base_id
        self._region = region

        config = boto_config or Config(
            region_name=region,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )

        self._bedrock_agent_runtime = boto3.client(
            "bedrock-agent-runtime", config=config
        )

        logger.info(
            "Bedrock document repository initialized",
            extra={"knowledge_base_id": knowledge_base_id, "region": region},
        )

    async def search_documents(
        self, query: str, max_results: int = 5
    ) -> list[DocumentChunk]:
        """
        Search documents using semantic search via Bedrock Knowledge Base.

        Args:
            query: Search query text
            max_results: Maximum number of results to return

        Returns:
            List of relevant document chunks ranked by relevance

        Raises:
            RuntimeError: If search operation fails
        """
        logger.info(
            "Searching documents in Bedrock KB",
            extra={"query": query, "max_results": max_results},
        )

        try:
            response = self._bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self._knowledge_base_id,
                retrievalQuery={"text": query},
                retrievalConfiguration={
                    "vectorSearchConfiguration": {"numberOfResults": max_results}
                },
            )

            chunks = []
            for idx, result in enumerate(response.get("retrievalResults", [])):
                content = result.get("content", {}).get("text", "")
                score = result.get("score", 0.0)
                metadata = result.get("metadata", {})

                # Extract document location/ID
                location = result.get("location", {})
                doc_id = location.get("s3Location", {}).get("uri", f"doc_{idx}")

                chunks.append(
                    DocumentChunk(
                        document_id=doc_id,
                        chunk_id=f"{doc_id}_chunk_{idx}",
                        content=content,
                        relevance_score=float(score),
                        metadata=metadata,
                    )
                )

            logger.info(
                "Document search completed",
                extra={
                    "results_count": len(chunks),
                    "avg_score": sum(c.relevance_score for c in chunks) / len(chunks) if chunks else 0,
                },
            )

            return chunks

        except Exception as e:
            logger.error(
                "Document search failed",
                extra={"error": str(e), "query": query},
                exc_info=True,
            )
            raise RuntimeError(f"Failed to search documents: {str(e)}")

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
        # Note: Bedrock Knowledge Base doesn't provide direct document retrieval by ID
        # This would require additional S3 integration or document tracking
        raise NotImplementedError(
            "Direct document retrieval by ID not implemented for Bedrock KB"
        )

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
        # Note: Bedrock Knowledge Base doesn't provide document listing API
        # This would require additional S3 integration or document tracking
        raise NotImplementedError(
            "Document listing not implemented for Bedrock KB"
        )
