"""Model for AI-generated analysis of differences between models."""
from typing import Dict, List, Optional
import os

from openai import AsyncOpenAI
from pydantic import BaseModel, ConfigDict, Field, model_validator

class LLMFindings(BaseModel):
    """AI-generated analysis of differences between models."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    findings: List[str] = Field(
        default_factory=list,
        description="Key findings from the analysis"
    )
    analysis: str = Field(
        default="",
        description="Detailed analysis of the differences"
    )

    @model_validator(mode="after")
    def validate_findings(self) -> "LLMFindings":
        """Ensure findings and analysis are not empty if present."""
        if self.findings and not self.analysis:
            raise ValueError("Analysis must be provided if findings exist")
        if self.analysis and not self.findings:
            raise ValueError("Findings must be provided if analysis exists")
        return self

    @classmethod
    async def analyze(
        cls,
        model_names: List[str],
        differences: Dict[str, Dict[str, str]]
    ) -> Optional["LLMFindings"]:
        """Generate analysis using GPT-3.5-turbo."""
        if not differences:
            return None

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        # Format differences for prompt
        diff_text = ""
        for category, specs in differences.items():
            diff_text += f"\n{category}:\n"
            for spec, values in specs.items():
                diff_text += f"- {spec}: {values}\n"

        # Construct prompt
        prompt = f"""You are a technical expert analyzing differences between relay models {' and '.join(model_names)}.

Here are the differences in specifications:
{diff_text}

Analyze these differences and provide:
1. A list of key findings (3-5 bullet points)
2. A detailed technical analysis explaining the implications of these differences

Focus on:
- Performance characteristics
- Operating conditions
- Design considerations
- Application suitability

Format the response as:
KEY FINDINGS:
- Finding 1
- Finding 2
- Finding 3

ANALYSIS:
[Your detailed analysis here]"""

        client = AsyncOpenAI(api_key=api_key)
        try:
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a technical expert in relay specifications and characteristics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            content = response.choices[0].message.content
            if not content:
                return None

            # Parse response
            parts = content.split("ANALYSIS:")
            if len(parts) != 2:
                return None

            findings_text, analysis = parts
            findings = [
                f.strip("- ").strip()
                for f in findings_text.split("KEY FINDINGS:")[1].strip().split("\n")
                if f.strip("- ").strip()
            ]

            return cls(
                findings=findings,
                analysis=analysis.strip()
            )

        except Exception:
            return None

    def get_summary(self) -> str:
        """Get a summary of the findings."""
        if not self.findings:
            return "No significant differences found."
        return "\n".join(f"• {finding}" for finding in self.findings)

    def get_details(self) -> str:
        """Get the detailed analysis."""
        if not self.analysis:
            return "No detailed analysis available."
        return self.analysis
