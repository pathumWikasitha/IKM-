"""Tests for serialization utilities."""

from langchain_core.documents import Document

from app.core.retrieval.serialization import serialize_chunks


def test_serialize_single_chunk():
    """Single document should produce 'Chunk 1 (page=X): ...' format."""
    docs = [Document(page_content="Hello world", metadata={"page": 1})]
    result = serialize_chunks(docs)
    assert "Chunk 1 (page=1):" in result
    assert "Hello world" in result


def test_serialize_multiple_chunks():
    """Multiple documents should be numbered sequentially."""
    docs = [
        Document(page_content="First", metadata={"page": 1}),
        Document(page_content="Second", metadata={"page": 2}),
        Document(page_content="Third", metadata={"page": 3}),
    ]
    result = serialize_chunks(docs)
    assert "Chunk 1 (page=1):" in result
    assert "Chunk 2 (page=2):" in result
    assert "Chunk 3 (page=3):" in result
    assert "First" in result
    assert "Third" in result


def test_serialize_empty_list():
    """Empty list should return empty string."""
    result = serialize_chunks([])
    assert result == ""


def test_serialize_missing_page_metadata():
    """Document without a page key should fall back to 'unknown'."""
    docs = [Document(page_content="No page", metadata={})]
    result = serialize_chunks(docs)
    assert "page=unknown" in result


def test_serialize_page_number_key():
    """Should also check for 'page_number' metadata key."""
    docs = [Document(page_content="Alternate key", metadata={"page_number": 42})]
    result = serialize_chunks(docs)
    assert "page=42" in result


def test_serialize_strips_whitespace():
    """Content should be stripped of leading/trailing whitespace."""
    docs = [Document(page_content="  padded content  ", metadata={"page": 1})]
    result = serialize_chunks(docs)
    assert "padded content" in result
    # Should not have leading/trailing spaces in the content part
    lines = result.split("\n")
    content_line = lines[1]  # second line is the content
    assert content_line == "padded content"
