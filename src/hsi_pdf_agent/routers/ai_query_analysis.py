"""Router for analysis endpoints."""
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List

from hsi_pdf_agent.models.ai_query_analysis import QueryAnalysis
from hsi_pdf_agent.models.ai_findings import AIFindings

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


class QueryRequest(BaseModel):
    """Request model for query analysis."""
    query: str


class CombinedRequest(BaseModel):
    """Request model for combined analysis."""
    query: str
    model_names: List[str]
    differences: Dict[str, Dict[str, str]]


@router.post("/query")
async def analyze_query(request: QueryRequest) -> QueryAnalysis:
    """Analyze a user query to determine display settings."""
    try:
        return await QueryAnalysis.analyze_query(request.query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/combined")
async def analyze_combined(request: CombinedRequest) -> Dict:
    """Combined endpoint for query analysis and AI findings."""
    try:
        # Get query analysis
        query_analysis = await QueryAnalysis.analyze_query(request.query)
        
        # Get AI findings
        findings = await AIFindings.analyze(request.model_names, request.differences)
        
        # Combine results
        return {
            "query_analysis": query_analysis,
            "findings": findings
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 