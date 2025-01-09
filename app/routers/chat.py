from fastapi import APIRouter, Depends, HTTPException
import logging
from ..core.chat_service import ChatService
from ..core.vector_store import VectorStore
from ..schemas.chat import ChatQuery, ChatResponse
from openai import OpenAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

async def get_chat_service() -> ChatService:
    """Dependency to get chat service instance."""
    openai_client = OpenAI()  # Uses OPENAI_API_KEY from environment
    vector_store = VectorStore(openai_client)
    return ChatService(vector_store, openai_client)

@router.post("/query", response_model=ChatResponse)
async def query(
    query: ChatQuery,
    chat_service: ChatService = Depends(get_chat_service)
) -> ChatResponse:
    """Query the PDFs using RAG.

    Args:
        query: The query parameters including the question
        chat_service: Chat service instance for handling the query

    Returns:
        ChatResponse containing just the answer
    """
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
