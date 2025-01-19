"""Models for LLM-based analysis of differences."""
import os
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from openai import AsyncOpenAI

from .differences import Differences


class LLMFindings(BaseModel):
    """AI-generated analysis of differences between models."""
    model_config = ConfigDict(extra="forbid")

    findings: Differences = Field(
        description="Collection of differences to analyze"
    )
    analysis: Optional[str] = Field(
        None,
        description="Generated analysis of the differences"
    )

    async def analyze(self) -> None:
        """Generate analysis using GPT-3.5-turbo."""
        try:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                self.analysis = (
                    "Error: OpenAI API key not found in environment"
                )
                return

            if not self.findings.has_differences():
                self.analysis = (
                    "No significant differences found between the models."
                )
                return

            # Format differences for GPT
            differences_text = []
            for diff in self.findings.differences:
                if not diff.has_differences():
                    continue
                values_text = ", ".join(
                    f"{model}: {value}"
                    for model, value in diff.values.items()
                    if value
                )
                differences_text.append(
                    f"{diff.category} - {diff.subcategory}: {values_text}"
                )

            if not differences_text:
                self.analysis = "No significant differences to analyze."
                return

            prompt = f"""Analyze the following differences between two models:

{chr(10).join(differences_text)}

Please provide your analysis in two clearly marked sections:

SUMMARY:
Provide a high-level overview of the key differences.
Focus on the most significant differences that impact choice.

DETAILED ANALYSIS:
Provide a point-by-point analysis of the specific differences:
1. Power and Current Handling
2. Voltage Characteristics
3. Operating Speed and Timing
4. Physical Characteristics
5. Other Notable Differences

For each point, explain the practical implications."""

            # Initialize OpenAI client with API key
            client = AsyncOpenAI(api_key=api_key)
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in analyzing technical specs."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=2000,
                presence_penalty=0.2,
                frequency_penalty=0.2
            )

            if not response.choices:
                self.analysis = "Failed to generate analysis."
                return

            content = response.choices[0].message.content
            if not content or not content.strip():
                self.analysis = "Failed to generate meaningful analysis."
                return

            self.analysis = content.strip()

        except Exception as e:
            self.analysis = f"Error generating analysis: {str(e)}"

    def get_summary(self) -> str:
        """Get the summary section of the analysis."""
        if not self.analysis:
            return "No analysis available"
        
        # Extract summary section (between SUMMARY: and DETAILED ANALYSIS:)
        lines = self.analysis.split("\n")
        summary_lines = []
        in_summary = False
        
        for line in lines:
            if line.strip().upper() == "SUMMARY:":
                in_summary = True
                continue
            if line.strip().upper() == "DETAILED ANALYSIS:":
                break
            if in_summary and line.strip():
                summary_lines.append(line)
        
        summary = "\n".join(summary_lines).strip()
        return summary if summary else "No summary available"

    def get_details(self) -> str:
        """Get the detailed section of the analysis."""
        if not self.analysis:
            return "No analysis available"
        
        # Extract details section (everything after DETAILED ANALYSIS:)
        lines = self.analysis.split("\n")
        details_lines = []
        in_details = False
        
        for line in lines:
            if line.strip().upper() == "DETAILED ANALYSIS:":
                in_details = True
                continue
            if in_details and line.strip():
                details_lines.append(line)
        
        details = "\n".join(details_lines).strip()
        return details if details else "No detailed analysis available"
