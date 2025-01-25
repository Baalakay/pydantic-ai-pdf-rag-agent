"""Models for query analysis."""
from typing import List, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict


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

    type: str = Field(..., pattern="^(single|comparison)$")
    models: List[str]
    specific_attribute: Optional[str] = None
    display_sections: DisplaySections
    focus: Optional[FocusSettings] = None

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
        from openai import AsyncOpenAI
        import os

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found")

        client = AsyncOpenAI(api_key=api_key)
        messages = [
            {
                "role": "system",
                "content": cls.SYSTEM_PROMPT + "\n\nRespond with a JSON object that exactly matches the structure shown in the example."
            },
            {
                "role": "user",
                "content": f"Analyze this query and respond with JSON: {query}"
            }
        ]

        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7
            )

            if not response.choices:
                raise ValueError("No response from OpenAI")

            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")

            # Parse the JSON response into our model
            import json
            data = json.loads(content)
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