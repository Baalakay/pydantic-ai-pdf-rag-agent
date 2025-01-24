"""Model for AI analysis findings."""
from typing import Dict, List, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
import os


class Recommendation(BaseModel):
    """Model for a single recommendation."""
    action: str = Field(..., description="The action verb (e.g., 'Choose', 'Select')")
    model: str = Field(..., description="The model being recommended")
    context: str = Field(..., description="The context or reason for the recommendation")
    category: str = Field(
        default="General Recommendations",
        description=(
            "Category of the recommendation (e.g., 'Performance', 'Design Considerations')"
        )
    )


class StructuredFindings(BaseModel):
    """Model for structured AI findings."""
    recommendations: List[Recommendation] = Field(
        ...,
        description="List of specific recommendations"
    )
    summary: str = Field(
        ...,
        description="Brief summary of key differences"
    )
    technical_details: str = Field(
        ...,
        description="Detailed technical analysis"
    )


class AIFindings(BaseModel):
    """Model for AI analysis findings."""
    model_config = ConfigDict(frozen=True)

    findings: StructuredFindings = Field(
        ...,
        description="Structured findings and recommendations"
    )

    SYSTEM_PROMPT: ClassVar[str] = """You are an expert magnetic sensor application specialist providing clear, actionable recommendations.
Your task is to analyze the differences between relay models and provide strong, opinionated guidance on model selection.

Focus your analysis on these key aspects:
1. Key performance differences
2. Operating condition variations
3. Design considerations
4. Application suitability

Your response must be a JSON object with this exact structure:
{
  "findings": {
    "recommendations": [
      {
        "action": "Choose",
        "model": "HSR-520R",
        "context": "for precision applications requiring fast response times under 2ms",
        "category": "Performance Considerations"
      },
      {
        "action": "Opt",
        "model": "HSR-637W",
        "context": "for high-power loads above 50W and maximum current requirements",
        "category": "Power Requirements"
      }
    ],
    "summary": "Brief overview of the key differences and selection criteria",
    "technical_details": "Detailed analysis of the technical specifications and their implications"
  }
}

Important:
- Every recommendation must use clear action verbs (Choose, Select, Consider, Use, Opt)
- Be specific about technical requirements and thresholds
- Provide clear, opinionated guidance
- Focus on helping engineers make decisive model selections
- Base recommendations on actual specification differences
- Group recommendations into meaningful categories

Be technical but clear. Make each recommendation actionable and specific."""

    @classmethod
    async def analyze(
        cls,
        model_names: List[str],
        differences: Dict[str, Dict[str, str]]
    ) -> "AIFindings":
        """Analyze differences between models using AI."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return cls(findings=StructuredFindings(
                recommendations=[],
                summary="No analysis available.",
                technical_details="No detailed analysis available."
            ))

        # Format differences for analysis
        diff_text = "Differences between models:\n\n"
        for spec, values in differences.items():
            diff_text += f"{spec}:\n"
            for model, value in values.items():
                diff_text += f"  {model}: {value}\n"
            diff_text += "\n"

        # Create chat completion request
        client = AsyncOpenAI(api_key=api_key)
        messages: List[ChatCompletionMessageParam] = [
            ChatCompletionSystemMessageParam(
                role="system",
                content=cls.SYSTEM_PROMPT + "\n\nRespond with a JSON object that exactly matches the structure shown in the example."
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    f"Please analyze these differences between "
                    f"relay models {', '.join(model_names)} and provide specific, "
                    f"actionable recommendations for model selection. Respond in JSON format:\n\n{diff_text}"
                )
            )
        ]

        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.7,
                max_tokens=2000
            )

            if not response.choices:
                return cls(findings=StructuredFindings(recommendations=[], summary="No analysis available.", technical_details="No detailed analysis available."))

            content = response.choices[0].message.content
            if not content:
                return cls(findings=StructuredFindings(recommendations=[], summary="No analysis available.", technical_details="No detailed analysis available."))

            # Parse the JSON response
            import json
            data = json.loads(content)
            return cls.model_validate(data)

        except Exception as e:
            print(f"Error during AI analysis: {str(e)}")
            return cls(findings=StructuredFindings(recommendations=[], summary="No analysis available.", technical_details="No detailed analysis available."))

    def get_summary(self) -> str:
        """Get the analysis summary."""
        return self.findings.summary if self.findings.summary else "No analysis available."

    def get_details(self) -> str:
        """Get the detailed analysis."""
        return self.findings.technical_details if self.findings.technical_details else "No detailed analysis available."
