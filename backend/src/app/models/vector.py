from typing import Dict, Any, List
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field


class VectorEntry(BaseModel):
    """Represents a vector entry in the vector store."""

    id: UUID = Field(
        ...,
        description="Unique identifier for the vector entry"
    )
    content: str = Field(
        ...,
        description="Text content of the entry"
    )
    embedding: List[float] = Field(
        ...,
        description="Vector embedding of the content"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
