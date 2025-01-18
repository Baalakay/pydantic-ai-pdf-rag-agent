"""Models for comparing model specifications."""
from typing import Dict, List, Optional
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.pdf import SectionData, SpecValue


class SpecRow(BaseModel):
    """A row in the specification comparison."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    category: Optional[str] = None
    specification: Optional[str] = None
    values: Dict[str, str] = Field(default_factory=dict)


class SpecsDataFrame(BaseModel):
    """A DataFrame for specification comparison."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    rows: List[SpecRow] = Field(default_factory=list)
    model_names: List[str] = Field(default_factory=list)
    
    def to_pandas(self) -> pd.DataFrame:
        """Convert to pandas DataFrame preserving order."""
        if not self.rows:
            return pd.DataFrame()
            
        data = []
        for row in self.rows:
            row_dict = {}
            if row.category is not None:
                row_dict["Category"] = row.category
            if row.specification is not None:
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


class ModelSpecs(BaseModel):
    """Specifications for a single model."""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    model_name: str = Field(description="Name of the model")
    features_advantages: Optional[Dict[str, List[str]]] = Field(
        None, description="Features and advantages"
    )
    sections: Dict[str, SectionData] = Field(
        description="Sections containing specifications"
    )


class ComparisonResult(BaseModel):
    """Result of comparing two or more models."""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    spec_differences_df: pd.DataFrame
    ai_analysis: Optional[Dict[str, str]] = None

    def format_dataframe(self, df: pd.DataFrame) -> str:
        """Format a DataFrame for display."""
        if df.empty:
            return ""

        # Calculate column widths based on content
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


def create_specs_df(
    models_data: List[ModelSpecs], 
    spec_type: str
) -> pd.DataFrame:
    """Create a DataFrame comparing specifications across models."""
    specs_df = SpecsDataFrame(model_names=[m.model_name for m in models_data])
    
    # Handle features and advantages
    if spec_type in ["features", "advantages"]:
        # Use first model with features/advantages as reference
        for model in models_data:
            if (model.features_advantages and 
                spec_type in model.features_advantages):
                for spec in model.features_advantages[spec_type]:
                    values = {}
                    for m in models_data:
                        has_spec = (
                            m.features_advantages and 
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
    
    return specs_df.to_pandas()


def compare_models(models_data: List[ModelSpecs]) -> ComparisonResult:
    """Compare specifications between models."""
    # Create differences DataFrame
    differences_df = pd.DataFrame()
    
    # Add specifications (excluding features and advantages)
    specs = [
        "Electrical_Specifications",
        "Magnetic_Specifications",
        "Physical_Operational_Specifications"
    ]
    
    for spec_type in specs:
        df = create_specs_df(models_data, spec_type)
        if not df.empty:
            differences_df = pd.concat([differences_df, df], ignore_index=True)
    
    return ComparisonResult(
        spec_differences_df=differences_df,
        ai_analysis=None
    )
