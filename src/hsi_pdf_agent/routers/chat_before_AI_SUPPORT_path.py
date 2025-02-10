"""Router for chat and query operations."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Literal, Union
from logfire import log

from hsi_pdf_agent.core.agents.cx_agent import (
    CXAgent, PSAgent, QueryAnalysis,
    ProductIntent, TechSupportIntent, CompanyIntent
)
from hsi_pdf_agent.core.config import get_openai_client

# Router definitions
chat_router = APIRouter(prefix="/chat", tags=["chat"])
query_router = APIRouter(prefix="/api", tags=["query"])

class QueryRequest(BaseModel):
    """Generic request for information."""
    query: str
    query_type: Literal["product", "techsupport", "company"] = "product"
    focus_areas: Optional[List[str]] = None
    preferences: Optional[Dict[str, bool]] = None

class QueryResponse(BaseModel):
    """Generic response containing query analysis and results."""
    query_type: Literal["product", "techsupport", "company"]
    intent: Union[ProductIntent, TechSupportIntent, CompanyIntent]
    data: Dict  # Query-specific structured data
    recommendations: Optional[Dict] = None
    metadata: Optional[Dict] = None  # Additional query-specific metadata

async def get_agents():
    """Get agent instances."""
    openai_client = get_openai_client()
    return CXAgent(openai_client), PSAgent(openai_client)

def validate_intent(analysis: QueryAnalysis) -> None:
    """Validate that the intent matches the query type."""
    intent_map = {
        "product": ProductIntent,
        "techsupport": TechSupportIntent,
        "company": CompanyIntent
    }
    
    try:
        # This will raise a ValueError if intent doesn't match the Literal type
        intent_type = intent_map[analysis.query_type]
        intent_type(analysis.intent)
    except (KeyError, ValueError):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid intent '{analysis.intent}' for query type '{analysis.query_type}'"
        )

@query_router.post("/query")
async def process_query(
    request: QueryRequest,
    agents: tuple[CXAgent, PSAgent] = Depends(get_agents)
) -> QueryResponse:
    """Process a query of any supported type."""
    cx_agent, ps_agent = agents
    
    try:
        # Analyze query intent
        analysis = await cx_agent.analyze_query(request.query)
        
        # Validate intent matches query type
        validate_intent(analysis)
        
        # Process based on query type
        if request.query_type == "product":
            if analysis.intent == "single":
                if not analysis.model_numbers:
                    raise HTTPException(
                        status_code=400,
                        detail="No model number found in query"
                    )
                result = await ps_agent.analyze_single_product(
                    analysis.model_numbers[0],
                    request.focus_areas
                )
                
            elif analysis.intent == "comparison":
                if len(analysis.model_numbers) < 2:
                    raise HTTPException(
                        status_code=400,
                        detail="At least two model numbers required for comparison"
                    )
                result = await ps_agent.compare_products(
                    analysis.model_numbers,
                    request.focus_areas
                )
                
            elif analysis.intent == "availability":
                if not analysis.model_numbers:
                    raise HTTPException(
                        status_code=400,
                        detail="No model number found for availability check"
                    )
                # TODO: Implement product availability check
                raise HTTPException(
                    status_code=501,
                    detail="Product availability check not yet implemented"
                )
                
            elif analysis.intent == "compatibility":
                if len(analysis.model_numbers) < 2:
                    raise HTTPException(
                        status_code=400,
                        detail="At least two model numbers required for compatibility check"
                    )
                # TODO: Implement compatibility check
                raise HTTPException(
                    status_code=501,
                    detail="Product compatibility check not yet implemented"
                )

        elif request.query_type == "techsupport":
            if not analysis.issue_description:
                raise HTTPException(
                    status_code=400,
                    detail="No issue description found in query"
                )
            # TODO: Implement tech support handling
            raise HTTPException(
                status_code=501,
                detail=f"Technical support ({analysis.intent}) not yet implemented"
            )

        elif request.query_type == "company":
            # TODO: Implement company information handling
            raise HTTPException(
                status_code=501,
                detail=f"Company information ({analysis.intent}) not yet implemented"
            )

        log.info(
            "query_processed",
            query_type=request.query_type,
            intent=analysis.intent,
            model_numbers=getattr(analysis, 'model_numbers', None)
        )

        return QueryResponse(
            query_type=request.query_type,
            intent=analysis.intent,
            data=result if 'result' in locals() else {},
            recommendations=result.get("recommendations") if 'result' in locals() else None,
            metadata={
                "model_numbers": getattr(analysis, 'model_numbers', None),
                "focus_areas": request.focus_areas,
                "preferences": request.preferences,
                "sentiment": analysis.sentiment,
                "urgency": analysis.urgency,
                "keywords": analysis.keywords
            }
        )

    except Exception as e:
        log.error(
            "query_processing_failed",
            error=str(e),
            query=request.query,
            query_type=request.query_type
        )
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=500,
            detail=f"Error processing query: {str(e)}"
        )
