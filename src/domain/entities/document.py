"""Document entity - represents financial documents in knowledge base."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Document:
    """Represents a document in the knowledge base."""

    id: str
    title: str
    content: str
    source_url: str
    document_type: str  # e.g., "annual_report", "earnings_release"
    company: str
    fiscal_period: Optional[str] = None  # e.g., "Q3 2025", "FY 2024"
    published_date: Optional[datetime] = None
    metadata: Optional[dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.id:
            raise ValueError("Document ID cannot be empty")
        if not self.title:
            raise ValueError("Document title cannot be empty")
        if not self.content:
            raise ValueError("Document content cannot be empty")
        if not self.company:
            raise ValueError("Company name cannot be empty")


@dataclass(frozen=True)
class DocumentChunk:
    """Represents a chunk of a document for RAG retrieval."""

    document_id: str
    chunk_id: str
    content: str
    relevance_score: float
    page_number: Optional[int] = None
    metadata: Optional[dict[str, str]] = None

    def __post_init__(self) -> None:
        """Validate entity invariants."""
        if not self.document_id:
            raise ValueError("Document ID cannot be empty")
        if not self.chunk_id:
            raise ValueError("Chunk ID cannot be empty")
        if not self.content:
            raise ValueError("Chunk content cannot be empty")
        if not 0 <= self.relevance_score <= 1:
            raise ValueError("Relevance score must be between 0 and 1")
