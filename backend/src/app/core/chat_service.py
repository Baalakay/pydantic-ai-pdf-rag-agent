from typing import List, Optional, cast, Literal, TypedDict
from uuid import uuid4
from datetime import datetime
import logfire
from openai import OpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from ..models import Message, Conversation, VectorEntry
from ..core.vector_store import VectorStore

MessageRole = Literal["user", "assistant", "system"]


class OpenAIMessage(TypedDict):
    role: MessageRole
    content: str
    name: Optional[str]


class ChatService:
    """Service for handling chat operations."""

    def __init__(self, vector_store: VectorStore, openai_client: OpenAI):
        self.vector_store = vector_store
        self.client = openai_client

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
            id=uuid4(),
            role=role,
            content=content,
            updated_at=datetime.utcnow()
        )
        conversation.messages.append(message)
        logfire.info(
            "message_added",
            conversation_id=str(conversation.id),
            message_id=str(message.id),
            role=role
        )
        return message

    async def get_relevant_context(
        self,
        question: str,
        max_sections: int = 3
    ) -> List[VectorEntry]:
        """Get relevant context for a question."""
        results = await self.vector_store.search(
            query=question,
            top_k=max_sections
        )
        context_entries = [entry for _, entry in results]
        logfire.info(
            "context_retrieved",
            query=question,
            num_sections=len(context_entries),
            max_sections=max_sections
        )
        return context_entries

    def _create_prompt(
        self,
        question: str,
        context_entries: List[VectorEntry]
    ) -> List[Message]:
        """Create a prompt for the chat model."""
        system_prompt = (
            "You are a helpful assistant that provides extremely concise answers based on the "
            "provided context. Your response must be formatted hierarchically based on the PDF sections, "
            "but only include the specific items that were asked about in the question.\n\n"
            "When asked about notes, look specifically at the bottom of the PDF for the numbered notes section. "
            "These notes contain important disclaimers and handling instructions, typically discussing "
            "informational purposes, factory consultation, handling care, and specification ranges. "
            "Format notes exactly as:\n"
            "Notes:\n"
            "\t(1) [exact text of first note]\n"
            "\t(2) [exact text of second note]\n"
            "\t(3) [exact text of third note]\n"
            "\t(4) [exact text of fourth note]\n\n"
            "For other queries, format your response like this:\n"
            "Device: [device/sensor model number]\n"
            "[Main Category (Electrical/Magnetic/Physical Specifications)]:\n"
            "\t[Subcategory (e.g., Power, Voltage, Temperature, etc.)]:\n"
            "\t\t[Specification]: [value with proper unit symbol]\n"
            "\t\t[Specification]: [value with proper unit symbol]\n"
            "(repeat for each specification section from the PDF, maintaining all subsections)\n\n"
            "For Features and Advantages sections:\n"
            "Features:\n"
            "\t- [feature point]\n"
            "Advantages:\n"
            "\t- [advantage point]\n\n"
            "Source: http://localhost:8000/pdf/download/[filename]\n\n"
            "Use tabs for indentation. Group related specifications together under their categories. "
            "Maintain the three main specification sections from the PDF:\n"
            "1. Electrical Specifications (power, voltage, current, resistance, etc.)\n"
            "2. Magnetic Specifications (pull-in range, test coil, etc.)\n"
            "3. Physical/Operational Specifications (temperature, timing, etc.)\n\n"
            "Use proper unit symbols:\n"
            "- Ohm: Ω\n"
            "- Voltage: V\n"
            "- Ampere: A\n"
            "- Watts: W\n"
            "- Temperature: °C\n"
            "- Picofarad: pF\n"
            "Only include items that were specifically asked about in the question. "
            "Maintain the exact section names as they appear in the PDF. "
            "If you cannot find a specific section in the context, indicate 'Section not found' "
            "rather than omitting it."
        )

        context_text = "\n\n".join(
            f"[Section {i + 1}]\n{entry.content}"
            for i, entry in enumerate(context_entries)
        )

        return [
            Message(
                id=uuid4(),
                role="system",
                content=system_prompt,
                updated_at=datetime.utcnow()
            ),
            Message(
                id=uuid4(),
                role="user",
                content=f"Context:\n{context_text}\n\nQuestion: {question}",
                updated_at=datetime.utcnow()
            )
        ]

    async def generate_response(
        self,
        question: str,
        conversation: Optional[Conversation] = None,
        max_context_sections: int = 3
    ) -> Message:
        """Generate a response to a question."""
        context_entries = await self.get_relevant_context(
            question=question,
            max_sections=max_context_sections
        )

        messages = self._create_prompt(question, context_entries)
        if conversation:
            messages.extend(conversation.messages)

        chat_messages = [
            cast(ChatCompletionMessageParam, {"role": msg.role, "content": msg.content})
            for msg in messages
        ]

        completion = self.client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=chat_messages,
            temperature=0.7
        )

        answer = cast(str, completion.choices[0].message.content)
        message = Message(
            id=uuid4(),
            role="assistant",
            content=answer,
            updated_at=datetime.utcnow()
        )

        if conversation:
            conversation.messages.append(message)

        logfire.info(
            "response_generated",
            question=question,
            response_id=str(message.id),
            conversation_id=str(conversation.id) if conversation else None
        )
        return message
