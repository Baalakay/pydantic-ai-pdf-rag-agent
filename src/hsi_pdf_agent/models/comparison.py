"""Data models for comparison functionality."""
from typing import Dict, List, Optional, ClassVar, Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator
import pandas as pd
import logging

from hsi_pdf_agent.models.ai_findings import AIFindings
from hsi_pdf_agent.models.features import ModelSpecs

logger = logging.getLogger(__name__)

SectionType = Literal["features", "advantages"]


class SpecDifference(BaseModel):
    """Represents a difference in specifications between models."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str = Field(description="Category of the specification")
    specification: str = Field(description="Name of the specification")
    values: Dict[str, str] = Field(description="Values for each model")


class SpecRow(BaseModel):
    """Represents a row in the specification comparison."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str = Field(
        default="",
        description="Category of the specification"
    )
    specification: str = Field(
        default="",
        description="Name of the specification"
    )
    values: Dict[str, str] = Field(
        default_factory=dict,
        description="Values for each model"
    )

    @model_validator(mode="before")
    @classmethod
    def validate_specification(cls, values):
        """Ensure specification is empty if it matches category."""
        if isinstance(values, dict):
            category = values.get("category", "").strip()
            specification = values.get("specification", "").strip()
            
            # If specification is empty or exactly matches category (case-sensitive),
            # set specification to empty string to preserve empty subcategory keys
            if (not specification or 
                specification == category or 
                specification.isspace() or
                (category == specification and category in [
                    "Test Coil", "Contact Material", "Release Time", "Pull - In Range"
                ])):
                values["specification"] = ""
        
        return values

    @model_validator(mode="before")
    @classmethod
    def validate_values(cls, values):
        """Ensure all values are properly formatted strings."""
        if isinstance(values, dict):
            value_dict = values.get("values", {})
            if not value_dict:
                raise ValueError("Values dictionary cannot be empty")
            values["values"] = {
                k.strip(): v.strip() if isinstance(v, str) else str(v)
                for k, v in value_dict.items()
                if k.strip()  # Only filter out empty keys, preserve empty values
            }
        return values


class SpecsDataFrame(BaseModel):
    """A DataFrame for specification comparison."""
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        extra="forbid"
    )

    rows: List[SpecRow] = Field(
        default_factory=list,
        description="Rows of specification data"
    )
    model_names: List[str] = Field(
        default_factory=list,
        description="Names of models being compared"
    )

    @classmethod
    def from_models(cls, models: List[ModelSpecs], section_name: str) -> 'SpecsDataFrame':
        """Create a DataFrame from a list of models."""
        # Validate model names
        model_names = [model.model_name for model in models]
        cls._validate_model_names(model_names)

        # Initialize empty rows list and spec_rows dict
        rows = []
        spec_rows: Dict[str, Dict[str, Dict[str, str]]] = {}

        # Process each model
        for model in models:
            # Get the section data
            section = model.sections.get(section_name)
            if not section:
                continue

            # Process each category in the section
            for category, cat_data in section.categories.items():
                if category not in spec_rows:
                    spec_rows[category] = {}

                # Process subcategories
                for subcat, spec_value in cat_data.subcategories.items():
                    # Always use empty string for specification when subcategory key is empty
                    spec_key = ""
                    if spec_key not in spec_rows[category]:
                        spec_rows[category][spec_key] = {}
                    
                    # Format the value with unit if present
                    display_value = str(spec_value.value)
                    if spec_value.unit:
                        display_value = f"{display_value} {spec_value.unit}"

                    spec_rows[category][spec_key][model.model_name] = display_value.strip()

        # Convert processed data to SpecRows
        for category, specs in spec_rows.items():
            for spec_name, values in specs.items():
                if values:  # Only create row if we have values
                    row = SpecRow(
                        category=category.strip(),
                        specification=spec_name,
                        values=values
                    )
                    rows.append(row)

        return cls(rows=rows, model_names=model_names)

    @model_validator(mode="after")
    def validate_model_names(self) -> "SpecsDataFrame":
        """Ensure model names are unique and non-empty."""
        if not self.model_names:
            raise ValueError("Model names list cannot be empty")
        if len(self.model_names) != len(set(self.model_names)):
            raise ValueError("Model names must be unique")
        return self

    def to_dataframe(self) -> pd.DataFrame:
        """Convert to pandas DataFrame preserving order."""
        if not self.rows:
            return pd.DataFrame()

        data = []
        for row in self.rows:
            row_dict = {}
            if row.category:
                row_dict["Category"] = row.category
            row_dict["Specification"] = row.specification
            row_dict.update(row.values)
            data.append(row_dict)

        df = pd.DataFrame(data)
        if df.empty:
            return df

        # Set column order
        cols = []
        if "Category" in df.columns:
            cols.append("Category")
        if "Specification" in df.columns:
            cols.append("Specification")
        cols.extend(self.model_names)

        return df[cols].fillna("")


class ComparisonResult(BaseModel):
    """Result of comparing multiple models."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    features_df: pd.DataFrame
    advantages_df: pd.DataFrame
    specs_df: pd.DataFrame
    spec_differences_df: pd.DataFrame
    findings: Optional[AIFindings] = None

    def model_dump(self, **kwargs) -> Dict:
        """Convert DataFrames to serializable format."""
        return {
            "features_df": self._convert_df(self.features_df),
            "advantages_df": self._convert_df(self.advantages_df),
            "specs_df": self._convert_df(self.specs_df),
            "spec_differences_df": self._convert_df(self.spec_differences_df),
            "findings": self.findings.model_dump() if self.findings else None
        }

    @staticmethod
    def _convert_df(df: pd.DataFrame) -> Dict:
        """Convert DataFrame to serializable format."""
        return {
            "columns": list(df.columns),
            "data": df.to_dict('records')
        }

    SPEC_SECTIONS: ClassVar[List[str]] = [
        "Electrical_Specifications",
        "Magnetic_Specifications",
        "Physical_Operational_Specifications"
    ]

    @model_validator(mode="after")
    def validate_differences(self) -> "ComparisonResult":
        """Ensure differences match the DataFrame."""
        if self.spec_differences_df.empty and self.differences.has_differences():
            raise ValueError(
                "Cannot have differences when DataFrame is empty"
            )
        return self

    def format_dataframe(self, df: pd.DataFrame) -> str:
        """Format a DataFrame for display."""
        if df.empty:
            return ""

        col_widths: Dict[str, int] = {}
        for col in df.columns:
            col_str = str(col)
            col_width = max(
                max(len(str(val)) for val in df[col]),
                len(col_str)
            ) + 2
            col_widths[col_str] = col_width

        rows: List[str] = []

        # Format header
        header = " | ".join(
            str(col).ljust(col_widths[str(col)])
            for col in df.columns
        )
        rows.append(header)
        rows.append("-" * len(header))

        # Format rows
        for _, row in df.iterrows():
            formatted_row = " | ".join(
                str(val).ljust(col_widths[str(col)])
                for col, val in row.items()
            )
            rows.append(formatted_row)

        return "\n".join(rows)

    def __str__(self) -> str:
        """Format the comparison result for display."""
        output = []

        # Format features
        if not self.features_df.empty:
            output.extend([
                "Features:",
                self.format_dataframe(self.features_df),
                ""
            ])

        # Format advantages
        if not self.advantages_df.empty:
            output.extend([
                "Advantages:",
                self.format_dataframe(self.advantages_df),
                ""
            ])

        # Format specifications
        if not self.specs_df.empty:
            output.extend([
                "Specifications:",
                self.format_dataframe(self.specs_df),
                ""
            ])

        # Format differences
        if not self.spec_differences_df.empty:
            output.extend([
                "Key Differences:",
                self.format_dataframe(self.spec_differences_df)
            ])

        # Add findings if available
        if self.findings and self.findings.findings:
            output.append("\nAI Analysis:")
            output.append(self.findings.findings.summary)
            output.append("\nRecommendations:")
            for rec in self.findings.findings.recommendations:
                output.append(f"- {rec.action} {rec.model} {rec.context}")

        return "\n".join(output) if output else "No data available."
