import pytest
from uuid import uuid4
from datetime import datetime
from openai import OpenAI
from app.core.vector_store import VectorStore
from app.core.chat_service import ChatService
from app.models import Message, Conversation, VectorEntry

@pytest.fixture
def openai_client() -> OpenAI:
    """Fixture for OpenAI client."""
    return OpenAI()

@pytest.fixture
def vector_store(openai_client: OpenAI) -> VectorStore:
    """Fixture for VectorStore instance."""
    return VectorStore(openai_client)

@pytest.fixture
def chat_service(vector_store: VectorStore, openai_client: OpenAI) -> ChatService:
    """Fixture for ChatService instance."""
    return ChatService(vector_store, openai_client)

@pytest.fixture
def sample_message() -> Message:
    """Fixture for a sample message."""
    return Message(
        id=uuid4(),
        role="user",
        content="Test message",
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_conversation(sample_message: Message) -> Conversation:
    """Fixture for a sample conversation."""
    return Conversation(
        id=uuid4(),
        title="Test Conversation",
        messages=[sample_message],
        updated_at=datetime.utcnow()
    )

@pytest.fixture
def sample_vector_entry() -> VectorEntry:
    """Fixture for a sample vector entry."""
    return VectorEntry(
        id=uuid4(),
        content="Test content",
        embedding=[0.1] * 1536,  # Typical embedding size
        model_name="text-embedding-3-small",
        updated_at=datetime.utcnow(),
        similarity_score=None
    )
