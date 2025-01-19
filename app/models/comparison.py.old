"""Comparison model for analyzing differences between models."""
from typing import ClassVar, Dict, List, TYPE_CHECKING

import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.config import get_settings
from app.models.pdf import PDFLocator
from app.models.differences import Differences
from app.models.llm_findings import LLMFindings
from app.models.features import ModelSpecs

if TYPE_CHECKING:
    from app.core.pdf_processor import PDFProcessor


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

    @model_validator(mode="after")
    def validate_values(self) -> "SpecRow":
        """Ensure all keys and values are non-empty strings."""
        if not self.values:
            raise ValueError("Values dictionary cannot be empty")
        self.values = {
            k.strip(): v.strip() 
            for k, v in self.values.items() 
            if k.strip() and v.strip()
        }
        return self


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

    @model_validator(mode="after")
    def validate_model_names(self) -> "SpecsDataFrame":
        """Ensure model names are unique and non-empty."""
        if not self.model_names:
            raise ValueError("Model names list cannot be empty")
        if len(self.model_names) != len(set(self.model_names)):
            raise ValueError("Model names must be unique")
        return self

    @classmethod
    def from_models(
        cls,
        models_data: List[ModelSpecs],
        spec_type: str
    ) -> pd.DataFrame:
        """Create a DataFrame from model specifications."""
        specs_df = cls(model_names=[m.model_name for m in models_data])

        # Handle features and advantages
        if spec_type in ["features", "advantages"]:
            # Use first model with features/advantages as reference
            for model in models_data:
                if spec_type in model.features_advantages:
                    for spec in model.features_advantages[spec_type]:
                        values = {}
                        for m in models_data:
                            has_spec = (
                                spec_type in m.features_advantages and
                                spec in m.features_advantages[spec_type]
                            )
                            values[m.model_name] = spec if has_spec else ""
                        specs_df.rows.append(SpecRow(values=values))
                    break

        # Handle regular specifications
        else:
            # Use first model with this section as reference
            reference_model = next(
                (m for m in models_data if spec_type in m.sections),
                None
            )

            if reference_model:
                section = reference_model.sections[spec_type]
                for cat_name, category in section.categories.items():
                    for subcat_name, subcategory in category.subcategories.items():
                        for spec_name, spec_value in subcategory.items():
                            spec_text = spec_name
                            if subcat_name and subcat_name.lower() != "general":
                                spec_text = f"{subcat_name} {spec_name}"

                            values = {}
                            for model in models_data:
                                value = ""
                                if spec_type in model.sections:
                                    m_section = model.sections[spec_type]
                                    m_cat = m_section.categories.get(cat_name)
                                    if m_cat:
                                        m_subcat = m_cat.subcategories.get(
                                            subcat_name
                                        )
                                        if m_subcat:
                                            m_spec = m_subcat.get(spec_name)
                                            if m_spec:
                                                value = (
                                                    f"{m_spec.value} {m_spec.unit}"
                                                    if m_spec.unit
                                                    else str(m_spec.value)
                                                )
                                values[model.model_name] = value

                            specs_df.rows.append(
                                SpecRow(
                                    category=cat_name,
                                    specification=spec_text,
                                    values=values
                                )
                            )

        return specs_df.to_dataframe()

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
    findings: LLMFindings | None = Field(
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

    @classmethod
    def from_models(cls, models_data: List[ModelSpecs]) -> "ComparisonResult":
        """Create a comparison result from model specifications."""
        # Create DataFrames for each section
        features_df = SpecsDataFrame.from_models(models_data, "features")
        advantages_df = SpecsDataFrame.from_models(models_data, "advantages")
        
        # Create specifications DataFrame
        specs_df = pd.DataFrame()
        differences_df = pd.DataFrame()
        differences = Differences()

        # Add specifications
        for spec_type in cls.SPEC_SECTIONS:
            df = SpecsDataFrame.from_models(models_data, spec_type)
            if not df.empty:
                specs_df = pd.concat([specs_df, df], ignore_index=True)
                
                # Collect differences for analysis
                for _, row in df.iterrows():
                    values = {
                        str(model): str(row[model]).strip()
                        for model in row.keys()
                        if model not in ["Category", "Specification"]
                        and str(row[model]).strip()
                    }
                    if len(set(values.values())) > 1:  # If values differ
                        # Add to differences DataFrame
                        differences_df = pd.concat(
                            [differences_df, pd.DataFrame([row])],
                            ignore_index=True
                        )
                        
                        # Extract unit from first non-empty value if present
                        unit = None
                        for val in values.values():
                            parts = val.split()
                            if len(parts) > 1:
                                unit = parts[-1]
                                break
                        
                        # Use Differences.add_difference method
                        differences.add_difference(
                            category=str(row.get("Category", "")),
                            subcategory=str(row.get("Specification", "")),
                            unit=unit,
                            values=values
                        )

        return cls(
            features_df=features_df,
            advantages_df=advantages_df,
            specs_df=specs_df,
            spec_differences_df=differences_df,
            differences=differences,
            findings=LLMFindings(
                findings=differences,
                analysis=None
            )
        )

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

    @classmethod
    def from_model_names(cls, model_names: List[str]) -> "ComparisonResult":
        """Create comparison from model names."""
        settings = get_settings()
        processor = PDFProcessor()
        locator = PDFLocator()
        
        # Process each model's PDF
        models = []
        for name in model_names:
            # Find PDF in uploads directory
            pdf_path = locator.find_pdf_by_model(name, settings.PDF_DIR)
            if not pdf_path:
                raise FileNotFoundError(f"PDF not found for model {name}")
            
            # Extract text and get actual model name
            text = processor._extract_text(str(pdf_path))
            model_name = processor._extract_model_name(text)
            if not model_name:
                raise ValueError(f"Could not extract model name from PDF {name}")
            
            # Process PDF and create ModelSpecs
            data = processor.extract_data(str(pdf_path))
            models.append(ModelSpecs(
                model_name=model_name,
                features_advantages=data.features_advantages or {},
                sections=data.sections
            ))
        
        # Create comparison from processed models
        return cls.from_models(models)
