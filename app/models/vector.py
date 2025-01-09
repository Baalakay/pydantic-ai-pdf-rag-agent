from typing import List, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field

class VectorEntry(BaseModel):
    """Represents a vector entry in the vector store."""
    id: UUID = Field(...)
    content: str = Field(...)
    embedding: List[float] = Field(...)
    model_name: str = Field(...)
    updated_at: datetime = Field(...)
    similarity_score: Optional[float] = Field(default=None)
    filename: str = Field(default="unknown")
    page_number: int = Field(default=1)
