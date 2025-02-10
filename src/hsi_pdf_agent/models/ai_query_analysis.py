"""Models for query analysis."""
from typing import List, Optional, ClassVar, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
import re
from ..core.ai_provider import Message as AIMessage, OllamaProvider
from ..core.chat_service import ChatService


class DisplaySections(BaseModel):
    """Configuration for which sections to display."""
    features: bool = Field(default=True)
    advantages: bool = Field(default=True)
    specifications: "SpecificationDisplay" = Field(
        default_factory=lambda: SpecificationDisplay(show=True, sections=[])
    )
    differences: "SpecificationDisplay" = Field(
        default_factory=lambda: SpecificationDisplay(show=False, sections=[])
    )


class SpecificationDisplay(BaseModel):
    """Configuration for specification display."""
    show: bool
    sections: List[str]


class FocusSettings(BaseModel):
    """Settings for focused analysis."""
    section: str
    category: Optional[str] = None
    attribute: Optional[str] = None


class QueryAnalysis(BaseModel):
    """Model for analyzing user queries."""
    model_config = ConfigDict(frozen=True)

    type: str = Field(..., description="Type of query - 'single' or 'comparison'")
    models: List[str] = Field(default_factory=list, description="List of model numbers to analyze")
    specific_attribute: Optional[str] = Field(None, description="Specific attribute to focus on")
    display_sections: dict = Field(
        default_factory=lambda: {
            "features": True,
            "advantages": True,
            "specifications": {
                "show": True,
                "sections": []
            },
            "differences": {
                "show": False,
                "sections": []
            }
        }
    )
    focus: Optional[dict] = None

    SYSTEM_PROMPT: ClassVar[str] = """You are an intelligent query analyzer for an HSR sensor model comparison system.
The system has these main sections:
1. Features (general product features)
2. Advantages (product benefits)
3. Specifications (organized into):
   - Electrical Specifications (power, voltage, current, resistance, capacitance)
   - Magnetic Specifications (pull-in range, test coil)
   - Physical/Operational Specifications (temperature, dimensions, timing)
4. Key Differences (highlighting variations between models)

Analyze user queries to determine:
1. Query type (single model or comparison)
2. Which models are being compared
3. What specific aspects they're interested in
4. Which sections should be displayed
5. Any specific focus areas within sections

Important rules:
- For comparison queries (2+ models), ALWAYS show the Key Differences section (differences.show = true)
- When showing differences, include ALL sections in differences.sections
- Only hide differences for single-model queries

Your response must be a JSON object with this exact structure:
{
  "type": "comparison",  // Must be either "single" or "comparison"
  "models": ["HSR-520R", "HSR-637W"],  // Array of model numbers found in query
  "specific_attribute": null,  // Optional specific attribute being queried
  "display_sections": {
    "features": true,
    "advantages": true,
    "specifications": {
      "show": true,
      "sections": ["Electrical Specifications", "Magnetic Specifications", "Physical/Operational Specifications"]
    },
    "differences": {
      "show": true,  // Must be true for comparison queries
      "sections": ["Electrical Specifications", "Magnetic Specifications", "Physical/Operational Specifications"]
    }
  },
  "focus": null  // Optional focus settings
}

Example query: "Compare HSR-520R and HSR-637W specifications"
Example response:
{
  "type": "comparison",
  "models": ["HSR-520R", "HSR-637W"],
  "specific_attribute": null,
  "display_sections": {
    "features": false,
    "advantages": false,
    "specifications": {
      "show": true,
      "sections": ["Electrical Specifications", "Magnetic Specifications", "Physical/Operational Specifications"]
    },
    "differences": {
      "show": true,
      "sections": ["Electrical Specifications", "Magnetic Specifications", "Physical/Operational Specifications"]
    }
  },
  "focus": {
    "section": "specifications"
  }
}"""

    @classmethod
    async def analyze_query(cls, query: str) -> "QueryAnalysis":
        """Analyze a user query to determine display settings."""
        chat_service = ChatService(provider=OllamaProvider())
        messages = [
            AIMessage(
                role="system",
                content=cls.SYSTEM_PROMPT + "\n\nRespond with a JSON object that exactly matches the structure shown in the example."
            ),
            AIMessage(
                role="user",
                content=f"Analyze this query and respond with JSON: {query}"
            )
        ]

        try:
            response = await chat_service.get_completion(messages)
            
            # Parse the JSON response into our model
            import json
            data = json.loads(response)
            return cls.model_validate(data)

        except Exception as e:
            print(f"Error during query analysis: {str(e)}")
            # Return a default analysis
            return cls(
                type="single",
                models=[],
                display_sections=DisplaySections(
                    features=True,
                    advantages=True,
                    specifications=SpecificationDisplay(show=True, sections=[]),
                    differences=SpecificationDisplay(show=False, sections=[])
                )
            )

    @classmethod
    def from_comparison(cls, model_numbers: List[str]) -> "QueryAnalysis":
        """Create analysis for a comparison query."""
        return cls(
            type="comparison",
            models=model_numbers,
            display_sections={
                "features": True,
                "advantages": True,
                "specifications": {
                    "show": True,
                    "sections": []
                },
                "differences": {
                    "show": True,  # Show differences for comparison
                    "sections": []
                }
            }
        )


class AIQueryAnalysis:
    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        messages = [
            AIMessage(
                role="system",
                content=QueryAnalysis.SYSTEM_PROMPT + "\n\nRespond with a JSON object that exactly matches the structure shown in the example."
            ),
            AIMessage(
                role="user",
                content=f"Analyze this query and respond with JSON: {query}"
            )
        ]
        
        try:
            response = await self.chat_service.get_completion(messages)
            
            # Parse the JSON response into our model
            import json
            data = json.loads(response)
            return QueryAnalysis.model_validate(data)

        except Exception as e:
            print(f"Error during query analysis: {str(e)}")
            # Return a default analysis
            return QueryAnalysis(
                type="single",
                models=[],
                display_sections=DisplaySections(
                    features=True,
                    advantages=True,
                    specifications=SpecificationDisplay(show=True, sections=[]),
                    differences=SpecificationDisplay(show=False, sections=[])
                )
            ) 