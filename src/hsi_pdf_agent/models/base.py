from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from uuid import UUID


class BaseDocument(BaseModel):
    """Base model for all documents."""
    id: UUID = Field(..., description="Unique identifier")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        None,
        description="Last update timestamp"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata"
    )

    class Config:
        from_attributes = True
