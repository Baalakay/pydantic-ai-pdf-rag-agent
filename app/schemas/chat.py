from pydantic import BaseModel, Field

class ChatQuery(BaseModel):
    """Schema for chat query request."""
    question: str = Field(..., description="The question to ask")
    max_context_sections: int = Field(
        default=3,
        description="Maximum number of context sections to use"
    )

class ChatResponse(BaseModel):
    """Schema for chat response."""
    answer: str = Field(..., description="Generated answer")
