"""Unit tests for Document entities."""
from datetime import datetime

import pytest

from src.domain.entities.document import Document, DocumentChunk


class TestDocument:
    """Tests for Document entity."""

    def test_create_valid_document(self):
        """Test creating a valid Document entity."""
        doc = Document(
            id="doc_123",
            title="Amazon Q3 2025 Earnings",
            content="Amazon reported strong Q3 results...",
            source_url="https://example.com/q3-earnings.pdf",
            document_type="earnings_release",
            company="Amazon",
            fiscal_period="Q3 2025",
            published_date=datetime(2025, 10, 26),
        )

        assert doc.id == "doc_123"
        assert doc.title == "Amazon Q3 2025 Earnings"
        assert doc.company == "Amazon"
        assert doc.fiscal_period == "Q3 2025"

    def test_document_immutable(self):
        """Test that Document is immutable."""
        doc = Document(
            id="doc_123",
            title="Test",
            content="Content",
            source_url="https://example.com",
            document_type="test",
            company="Amazon",
        )

        with pytest.raises(AttributeError):
            doc.title = "New Title"  # type: ignore

    def test_empty_id_raises_error(self):
        """Test that empty ID raises ValueError."""
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            Document(
                id="",
                title="Test",
                content="Content",
                source_url="https://example.com",
                document_type="test",
                company="Amazon",
            )

    def test_empty_title_raises_error(self):
        """Test that empty title raises ValueError."""
        with pytest.raises(ValueError, match="Document title cannot be empty"):
            Document(
                id="doc_123",
                title="",
                content="Content",
                source_url="https://example.com",
                document_type="test",
                company="Amazon",
            )

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Document content cannot be empty"):
            Document(
                id="doc_123",
                title="Test",
                content="",
                source_url="https://example.com",
                document_type="test",
                company="Amazon",
            )

    def test_empty_company_raises_error(self):
        """Test that empty company raises ValueError."""
        with pytest.raises(ValueError, match="Company name cannot be empty"):
            Document(
                id="doc_123",
                title="Test",
                content="Content",
                source_url="https://example.com",
                document_type="test",
                company="",
            )

    def test_optional_fields(self):
        """Test that optional fields work correctly."""
        doc = Document(
            id="doc_123",
            title="Test",
            content="Content",
            source_url="https://example.com",
            document_type="test",
            company="Amazon",
            metadata={"key": "value"},
        )

        assert doc.metadata == {"key": "value"}
        assert doc.fiscal_period is None
        assert doc.published_date is None


class TestDocumentChunk:
    """Tests for DocumentChunk entity."""

    def test_create_valid_document_chunk(self):
        """Test creating a valid DocumentChunk entity."""
        chunk = DocumentChunk(
            document_id="doc_123",
            chunk_id="chunk_1",
            content="This is a chunk of the document...",
            relevance_score=0.95,
            page_number=5,
        )

        assert chunk.document_id == "doc_123"
        assert chunk.chunk_id == "chunk_1"
        assert chunk.relevance_score == 0.95
        assert chunk.page_number == 5

    def test_empty_document_id_raises_error(self):
        """Test that empty document_id raises ValueError."""
        with pytest.raises(ValueError, match="Document ID cannot be empty"):
            DocumentChunk(
                document_id="",
                chunk_id="chunk_1",
                content="Content",
                relevance_score=0.95,
            )

    def test_empty_chunk_id_raises_error(self):
        """Test that empty chunk_id raises ValueError."""
        with pytest.raises(ValueError, match="Chunk ID cannot be empty"):
            DocumentChunk(
                document_id="doc_123",
                chunk_id="",
                content="Content",
                relevance_score=0.95,
            )

    def test_empty_content_raises_error(self):
        """Test that empty content raises ValueError."""
        with pytest.raises(ValueError, match="Chunk content cannot be empty"):
            DocumentChunk(
                document_id="doc_123",
                chunk_id="chunk_1",
                content="",
                relevance_score=0.95,
            )

    def test_invalid_relevance_score_raises_error(self):
        """Test that invalid relevance score raises ValueError."""
        # Score > 1
        with pytest.raises(ValueError, match="Relevance score must be between 0 and 1"):
            DocumentChunk(
                document_id="doc_123",
                chunk_id="chunk_1",
                content="Content",
                relevance_score=1.5,
            )

        # Score < 0
        with pytest.raises(ValueError, match="Relevance score must be between 0 and 1"):
            DocumentChunk(
                document_id="doc_123",
                chunk_id="chunk_1",
                content="Content",
                relevance_score=-0.5,
            )

    def test_valid_relevance_score_boundaries(self):
        """Test that boundary values (0 and 1) are valid."""
        chunk_0 = DocumentChunk(
            document_id="doc_123",
            chunk_id="chunk_1",
            content="Content",
            relevance_score=0.0,
        )
        assert chunk_0.relevance_score == 0.0

        chunk_1 = DocumentChunk(
            document_id="doc_123",
            chunk_id="chunk_1",
            content="Content",
            relevance_score=1.0,
        )
        assert chunk_1.relevance_score == 1.0
