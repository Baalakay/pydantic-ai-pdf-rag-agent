from fastapi import APIRouter, Depends, HTTPException
import logging
from openai import OpenAI
from pydantic import BaseModel
from typing import List

from hsi_pdf_agent.core.chat_service import ChatService
from hsi_pdf_agent.core.vector_store import VectorStore
from hsi_pdf_agent.schemas.chat import ChatQuery, ChatResponse
from hsi_pdf_agent.core.process_compare import ComparisonProcessor

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["chat"])
compare_router = APIRouter(prefix="/api", tags=["comparison"])

class ComparisonRequest(BaseModel):
    """Request model for model comparison."""
    model_numbers: List[str]

async def get_chat_service() -> ChatService:
    """Dependency to get chat service instance."""
    openai_client = OpenAI()  # Uses OPENAI_API_KEY from environment
    vector_store = VectorStore(openai_client)
    return ChatService(vector_store, openai_client)

@chat_router.post("/query", response_model=ChatResponse)
async def query(
    query: ChatQuery,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Query the PDFs using RAG."""
    try:
        response = await chat_service.generate_response(
            question=query.question,
            max_context_sections=query.max_context_sections
        )

        return ChatResponse(answer=response.content)
    except Exception as e:
        logger.error(f"Error processing chat query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Error processing your question"
        )

@compare_router.post("/compare")
async def compare_models(request: ComparisonRequest) -> dict:
    """Compare specifications between models."""
    try:
        processor = ComparisonProcessor()
        result = await processor.compare_models(request.model_numbers)
        return result.model_dump()
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing models: {str(e)}"
        )
