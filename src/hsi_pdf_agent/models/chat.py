from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class Message(BaseModel):
    id: str = Field(..., description="Unique identifier for the message")
    role: str = Field(
        ...,
        description="Role of the message sender (system, user, assistant)"
    )
    content: str = Field(..., description="Content of the message")
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Conversation(BaseModel):
    id: str = Field(..., description="Unique identifier for the conversation")
    messages: List[Message] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: dict = Field(default_factory=dict)
