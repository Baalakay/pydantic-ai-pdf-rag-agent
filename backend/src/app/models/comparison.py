"""Data models for comparison functionality."""
from typing import Dict, List, Optional, ClassVar, Literal, Any
from pydantic import BaseModel, ConfigDict, Field, model_validator
import pandas as pd

from .differences import Differences
from .ai_findings import AIFindings
from .features import ModelSpecs

SectionType = Literal["features", "advantages"]


class SpecDifference(BaseModel):
    """Represents a difference in specifications between models."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    category: str = Field(description="Category of the specification")
    specification: str = Field(description="Name of the specification")
    values: Dict[str, str] = Field(description="Values for each model")


class SpecRow(BaseModel):
    """A row in the specification comparison."""
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
    def validate_values(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all keys and values are non-empty strings."""
        values = data.get("values", {})
        if not values:
            raise ValueError("Values dictionary cannot be empty")
        data["values"] = {
            k.strip(): v.strip()
            for k, v in values.items()
            if k.strip() and v.strip()
        }
        return data


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
    def from_models(cls, models: List[ModelSpecs], section_name: str) -> pd.DataFrame:
        """Create DataFrame from model specifications for a given section."""
        if not models:
            return pd.DataFrame()
        model_names = [model.model_name for model in models]
        rows: List[SpecRow] = []

        if section_name in ("features", "advantages"):
            # Create a mapping of features/advantages to their models
            item_models: Dict[str, List[str]] = {}
            for model in models:
                if not model.features_advantages:
                    continue
                items = model.features_advantages.get(section_name, [])
                for item in items:
                    if item not in item_models:
                        item_models[item] = []
                    item_models[item].append(model.model_name)

            # Create SpecRow for each unique item
            for item, model_list in item_models.items():
                # Clean values before creating SpecRow
                values = {
                    model.strip(): "✓"
                    for model in model_list
                    if model.strip()
                }
                if values:  # Only create row if we have valid values
                    rows.append(SpecRow(
                        specification=item.strip(),
                        values=values
                    ))
            return cls(rows=rows, model_names=model_names).to_dataframe()

        # Process specification sections
        spec_rows: Dict[str, Dict[str, Dict[str, str]]] = {}
        for model in models:
            if not model.sections:
                continue
            section = model.sections.get(section_name)
            if not section:
                continue

            # Process each category in the section
            for category, cat_data in section.categories.items():
                if category not in spec_rows:
                    spec_rows[category] = {}

                # Process subcategories
                for subcat, spec_value in cat_data.subcategories.items():
                    spec_key = subcat if subcat else category
                    if spec_key not in spec_rows[category]:
                        spec_rows[category][spec_key] = {}

                    # Format the value with unit if present
                    display_value = str(spec_value.value)
                    if spec_value.unit:
                        display_value = f"{display_value} {spec_value.unit}"

                    spec_rows[category][spec_key][model.model_name] = display_value.strip()

        # Convert processed data to SpecRows
        for category, subcats in spec_rows.items():
            for spec_name, values in subcats.items():
                if values:  # Only create row if we have values
                    rows.append(SpecRow(
                        category=category.strip(),
                        specification=spec_name.strip(),
                        values=values
                    ))

        return cls(rows=rows, model_names=model_names).to_dataframe()

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
            if row.specification:
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
    """Result of comparing two or more models."""
    model_config = ConfigDict(
        frozen=True,
        arbitrary_types_allowed=True,
        extra="forbid"
    )

    features_df: pd.DataFrame = Field(
        default_factory=pd.DataFrame,
        description="DataFrame containing features"
    )
    advantages_df: pd.DataFrame = Field(
        default_factory=pd.DataFrame,
        description="DataFrame containing advantages"
    )
    specs_df: pd.DataFrame = Field(
        default_factory=pd.DataFrame,
        description="DataFrame containing all specifications"
    )
    spec_differences_df: pd.DataFrame = Field(
        default_factory=pd.DataFrame,
        description="DataFrame containing differences"
    )
    differences: Differences = Field(
        default_factory=Differences,
        description="Collection of differences between models"
    )
    findings: Optional[AIFindings] = Field(
        default=None,
        description="AI analysis of the differences"
    )

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

        # Format AI analysis if available
        if self.findings and self.findings.analysis:
            output.extend([
                "",
                "AI Analysis:",
                "",
                "Summary:",
                self.findings.get_summary(),
                "",
                "Detailed Analysis:",
                self.findings.get_details()
            ])

        return "\n".join(output) if output else "No data available."
