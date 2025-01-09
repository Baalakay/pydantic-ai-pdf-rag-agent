import pytest
from datetime import datetime
from uuid import UUID
from app.core.vector_store import VectorStore
from app.models import VectorEntry

@pytest.mark.asyncio
async def test_add_entry(vector_store: VectorStore) -> None:
    """Test adding an entry to the vector store."""
    entry = await vector_store.add_entry("Test content")

    assert entry.content == "Test content"
    assert isinstance(entry.id, UUID)
    assert isinstance(entry.updated_at, datetime)
    assert isinstance(entry.embedding, list)
    assert len(entry.embedding) == 1536  # text-embedding-3-small dimension
    assert entry.model_name == "text-embedding-3-small"
    assert entry.similarity_score is None

@pytest.mark.asyncio
async def test_search_empty_store(vector_store: VectorStore) -> None:
    """Test searching when store is empty."""
    results = await vector_store.search("test query")
    assert len(results) == 0

@pytest.mark.asyncio
async def test_search_with_entries(
    vector_store: VectorStore,
    sample_vector_entry: VectorEntry
) -> None:
    """Test searching with entries in store."""
    vector_store.entries.append(sample_vector_entry)
    results = await vector_store.search("test query", top_k=1)

    assert len(results) == 1
    similarity, entry = results[0]
    assert isinstance(similarity, float)
    assert entry.id == sample_vector_entry.id
