from datetime import datetime
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from uuid import UUID


class Embedding(BaseModel):
    """Model for stored embeddings."""
    id: UUID = Field(..., description="Unique identifier for the embedding")
    content: str = Field(..., description="Original text content")
    vector: List[float] = Field(..., description="Embedding vector")
    model: str = Field(..., description="Model used to generate the embedding")
    pdf_id: UUID = Field(..., description="ID of the PDF this embedding is from")
    page_number: int = Field(..., description="Page number in the PDF")
    section_number: int = Field(..., description="Section number in the page")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the embedding was created"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional embedding metadata"
    )

    class Config:
        from_attributes = True
