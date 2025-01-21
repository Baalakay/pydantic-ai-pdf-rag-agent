import pytest
from datetime import datetime
from uuid import UUID
from backend.src.app.core.chat_service import ChatService
from backend.src.app.models import Conversation, Message

@pytest.mark.asyncio
async def test_create_conversation(chat_service: ChatService) -> None:
    """Test creating a new conversation."""
    conversation = await chat_service.create_conversation("Test Chat")

    assert conversation.title == "Test Chat"
    assert isinstance(conversation.id, UUID)
    assert isinstance(conversation.created_at, datetime)
    assert isinstance(conversation.updated_at, datetime)
    assert len(conversation.messages) == 0

@pytest.mark.asyncio
async def test_add_message(
    chat_service: ChatService,
    sample_conversation: Conversation
) -> None:
    """Test adding a message to a conversation."""
    message = await chat_service.add_message(
        conversation=sample_conversation,
        role="user",
        content="Hello!"
    )

    assert message.role == "user"
    assert message.content == "Hello!"
    assert isinstance(message.id, UUID)
    assert isinstance(message.created_at, datetime)
    assert isinstance(message.updated_at, datetime)
    assert len(sample_conversation.messages) == 2  # Including the sample message
