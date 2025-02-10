from fastapi import APIRouter, Depends, HTTPException
import logging
from typing import List
from pydantic import BaseModel

from hsi_pdf_agent.core.chat_service import ChatService
from hsi_pdf_agent.schemas.chat import ChatQuery, ChatResponse
from hsi_pdf_agent.core.process_compare import ComparisonProcessor
from hsi_pdf_agent.core.ai_provider import OllamaProvider

logger = logging.getLogger(__name__)

chat_router = APIRouter(prefix="/chat", tags=["chat"])
compare_router = APIRouter(prefix="/api", tags=["comparison"])

class ComparisonRequest(BaseModel):
    """Request model for model comparison."""
    model_numbers: List[str]

async def get_chat_service() -> ChatService:
    """Dependency to get chat service instance."""
    provider = OllamaProvider()
    return ChatService(provider=provider)

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
            detail="Error processing your question dawg!"
        )

@compare_router.post("/compare")
async def compare_models(request: ComparisonRequest) -> dict:
    """Compare specifications between models."""
    try:
        processor = ComparisonProcessor()
        result = await processor.compare_models(request.model_numbers)
        
        if result.specs_df.empty:
            return {
                "specifications": {
                    "columns": ["Category", "Specification"],
                    "data": []
                },
                "differences": {
                    "columns": ["Category", "Specification"],
                    "data": []
                },
                "features": {
                    "columns": ["Category", "Specification"],
                    "data": []
                },
                "advantages": {
                    "columns": ["Category", "Specification"],
                    "data": []
                },
                "findings": None
            }
        
        # Transform specs_df to frontend format
        specs_data = {
            "columns": ["Category", "Specification"] + request.model_numbers,
            "data": result.specs_df.to_dict('records')
        }
        
        # Transform features and advantages
        features_data = {
            "columns": ["Category", "Specification"] + request.model_numbers,
            "data": result.features_df.to_dict('records') if not result.features_df.empty else []
        }
        
        advantages_data = {
            "columns": ["Category", "Specification"] + request.model_numbers,
            "data": result.advantages_df.to_dict('records') if not result.advantages_df.empty else []
        }
        
        return {
            "specifications": specs_data,
            "differences": {
                "columns": ["Category", "Specification"] + request.model_numbers,
                "data": result.spec_differences_df.to_dict('records') if not result.spec_differences_df.empty else []
            },
            "features": features_data,
            "advantages": advantages_data,
            "findings": result.findings.dict() if result.findings else None
        }
    except Exception as e:
        logger.error(f"Error comparing models: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error comparing models: {str(e)}"
        )
