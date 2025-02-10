from typing import List, Optional, cast, Literal, TypedDict
from uuid import uuid4
from datetime import datetime
import logfire
from pydantic import BaseModel

from hsi_pdf_agent.models.chat import Message, Conversation
from .ai_provider import AIProvider, OllamaProvider

MessageRole = Literal["user", "assistant", "system"]


class OpenAIMessage(TypedDict):
    role: MessageRole
    content: str
    name: Optional[str]


class ChatService:
    """Service for handling chat operations."""

    def __init__(self, provider: Optional[AIProvider] = None):
        self.provider = provider or OllamaProvider()

    async def create_conversation(self, title: str) -> Conversation:
        """Create a new conversation."""
        conversation = Conversation(
            id=uuid4(),
            title=title,
            updated_at=datetime.utcnow()
        )
        logfire.info(
            "conversation_created",
            conversation_id=str(conversation.id)
        )
        return conversation

    async def add_message(
        self,
        conversation: Conversation,
        role: MessageRole,
        content: str
    ) -> Message:
        """Add a message to a conversation."""
        message = Message(
            id=str(uuid4()),
            role=role,
            content=content,
            updated_at=datetime.utcnow()
        )
        conversation.messages.append(message)
        logfire.info(
            "message_added",
            conversation_id=str(conversation.id),
            message_id=message.id,
            role=role
        )
        return message

    async def generate_response(
        self,
        question: str,
        conversation: Optional[Conversation] = None,
        max_context_sections: int = 3
    ) -> Message:
        """Generate a response to a question."""
        messages = [
            Message(
                id=str(uuid4()),
                role="user",
                content=question,
                updated_at=datetime.utcnow()
            )
        ]
        if conversation:
            messages.extend(conversation.messages)

        # Convert our Message objects to the format expected by the provider
        from .ai_provider import Message as AIMessage
        chat_messages = [
            AIMessage(role=msg.role, content=msg.content)
            for msg in messages
        ]

        completion = await self.provider.complete(chat_messages)

        answer = completion.answer
        message = Message(
            id=str(uuid4()),
            role="assistant",
            content=answer,
            updated_at=datetime.utcnow()
        )

        if conversation:
            conversation.messages.append(message)

        logfire.info(
            "response_generated",
            question=question,
            response_id=message.id,
            conversation_id=str(conversation.id) if conversation else None
        )
        return message

    async def get_completion(self, messages: List[Message], **kwargs) -> str:
        # Convert our Message objects to the format expected by the provider
        from .ai_provider import Message as AIMessage
        chat_messages = [
            AIMessage(role=msg.role, content=msg.content)
            for msg in messages
        ]
        response = await self.provider.complete(chat_messages, **kwargs)
        
        # Clean up response before returning
        cleaned_response = (response.answer
            .replace("<think>", "")
            .replace("</think>", "")
            .strip())
            
        return cleaned_response
