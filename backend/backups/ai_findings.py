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

    SYSTEM_PROMPT: ClassVar[str] = """You are an expert magnetic sensor application specialist providing clear, actionable recommendations.
Your task is to analyze the differences between relay models and provide strong, opinionated guidance on model selection.

Focus on providing clear, action-oriented recommendations that:
1. Start with verbs like "Choose", "Opt for", "Consider", "Select", or "Use"
2. Include specific context about operating conditions or performance requirements
3. Explain the technical reasoning behind each recommendation

For example:
- "Choose Model X for high-precision applications requiring fast response times under 2ms"
- "Opt for Model Y in high-power industrial environments due to its superior current handling"
- "Consider Model Z for applications with varying magnetic fields due to its wider pull-in range"

Organize your response into:
1. A focused summary of key selection criteria
2. Specific, actionable recommendations for different use cases
3. Technical implications that impact model selection

Be technical but clear. Focus on helping engineers make informed decisions based on their specific requirements."""

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
                    f"relay models {', '.join(model_names)} and provide specific, "
                    f"actionable recommendations for model selection:\n\n{diff_text}"
                )
            )
        ]

        try:
            response = await client.chat.completions.create(
                model="gpt-4-turbo-preview",
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
