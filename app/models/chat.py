from typing import List, Literal
from pydantic import Field
from .base import BaseDocument

class Message(BaseDocument):
    """Model for a chat message."""
    role: Literal["user", "assistant", "system"] = Field(
        ...,
        description="Role of the message sender"
    )
    content: str = Field(..., description="Content of the message")

class Conversation(BaseDocument):
    """Model for a chat conversation."""
    title: str = Field(..., description="Title of the conversation")
    messages: List[Message] = Field(
        default_factory=list,
        description="Messages in the conversation"
    )
