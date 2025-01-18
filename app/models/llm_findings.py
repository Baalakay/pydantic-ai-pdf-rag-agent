"""Models for LLM-based analysis of differences."""
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict

from .differences import Differences


class AIAnalysis(BaseModel):
    """AI-generated analysis of differences between models."""
    model_config = ConfigDict(validate_assignment=True)

    findings: Differences = Field(description="Collection of differences to analyze")
    analysis: Optional[str] = Field(
        None,
        description="Generated analysis of the differences"
    )

    def generate_analysis(self) -> str:
        """Generate analysis of differences between models."""
        # Debug print to check differences
        print(f"Number of differences: {len(self.findings.differences)}")
        for diff in self.findings.differences:
            print(f"Difference has differences: {diff.has_differences()}")
            
        if not self.findings.has_differences():
            return "No significant differences found between the models."
            
        # Format findings into text
        findings_text = ""
        for diff in self.findings.differences:
            if not diff.has_differences():
                continue
                
            values_text = ", ".join(
                f"{model}: {value}"
                for model, value in diff.values.items()
                if value
            )
            findings_text += (
                f"{diff.category} - {diff.subcategory}: {values_text}\n"
            )
            
        return findings_text 