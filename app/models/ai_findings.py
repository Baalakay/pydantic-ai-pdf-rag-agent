"""Model for AI analysis findings."""
from typing import Dict, List, Optional, ClassVar
from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam
)
import os


class AIFindings(BaseModel):
    """Model for AI analysis findings."""
    model_config = ConfigDict(frozen=True)

    analysis: Optional[str] = Field(
        None,
        description="AI analysis of the differences"
    )
    summary: Optional[str] = Field(
        None,
        description="Summary of key differences"
    )
    details: Optional[str] = Field(
        None,
        description="Detailed analysis of differences"
    )

    SYSTEM_PROMPT: ClassVar[str] = """You are an expert in magnetic sensor application, specifications and technical
analysis. Your task is to analyze the differences between these models and provide insights into their implications.
Focus on:
1. Key performance differences
2. Operating condition variations
3. Design considerations
4. Application suitability

Format your response with:
- A brief summary of the most significant differences
- A detailed analysis organized by categories
- Technical implications of the differences
- Recommendations for different use cases

Be technical but clear. Use bullet points and sections for organization."""

    @classmethod
    async def analyze(
        cls,
        model_names: List[str],
        differences: Dict[str, Dict[str, str]]
    ) -> "AIFindings":
        """Analyze differences between models using AI."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return cls(analysis=None, summary=None, details=None)

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
                content=cls.SYSTEM_PROMPT
            ),
            ChatCompletionUserMessageParam(
                role="user",
                content=(
                    f"Please analyze these differences between "
                    f"relay models {', '.join(model_names)}:\n\n{diff_text}"
                )
            )
        ]

        try:
            response = await client.chat.completions.create(
                # model="gpt-4-turbo-preview",
                model="gpt-3.5-turbo",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            if not response.choices:
                return cls(analysis=None, summary=None, details=None)

            analysis = response.choices[0].message.content
            if not analysis:
                return cls(analysis=None, summary=None, details=None)

            # Split analysis into summary and details
            parts = analysis.split("\n\n", 1)
            summary = parts[0].replace("Summary:", "").strip()
            details = parts[1] if len(parts) > 1 else ""

            return cls(
                analysis=analysis,
                summary=summary,
                details=details
            )

        except Exception as e:
            print(f"Error during AI analysis: {str(e)}")
            return cls(analysis=None, summary=None, details=None)

    def get_summary(self) -> str:
        """Get the analysis summary."""
        return self.summary if self.summary else "No analysis available."

    def get_details(self) -> str:
        """Get the detailed analysis."""
        return self.details if self.details else "No detailed analysis available."
