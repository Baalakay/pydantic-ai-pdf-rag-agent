"""Models for specification differences between models."""
from typing import List, Optional, Dict
from pydantic import BaseModel, Field, ConfigDict
import pandas as pd


class Difference(BaseModel):
    """A single difference between two models."""
    model_config = ConfigDict(frozen=True)

    category: str = Field(description="Category of the specification")
    subcategory: str = Field(description="Subcategory of the specification")
    unit: Optional[str] = Field(None, description="Unit of measurement")
    values: Dict[str, str] = Field(description="Model-specific values")

    def has_differences(self) -> bool:
        """Check if there are actual differences in values."""
        unique_values = {v for v in self.values.values() if v}
        return len(unique_values) > 1


class Differences(BaseModel):
    """Collection of differences between models."""
    model_config = ConfigDict(validate_assignment=True)

    differences: List[Difference] = Field(
        default_factory=list,
        description="List of differences between models"
    )

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "Differences":
        """Create from a pandas DataFrame."""
        differences = []
        if df.empty:
            return cls(differences=differences)
            
        # Get model columns (non-metadata columns)
        model_cols = [col for col in df.columns 
                     if col not in ["Category", "Specification"]]
        
        # Process each row
        for _, row in df.iterrows():
            # Get model-specific values
            values = {
                model: str(row[model]).strip()
                for model in model_cols
                if (str(row[model]).strip() and 
                    str(row[model]).lower() != 'nan')
            }
            
            if len(values) < 2:  # Skip if not enough models have values
                continue
                
            # Split specification into parts
            spec = row["Specification"]
            unit = None
            if "(" in spec and ")" in spec:
                # Extract unit from parentheses
                unit_start = spec.rfind("(")
                unit_end = spec.rfind(")")
                if unit_start > 0 and unit_end > unit_start:
                    unit = spec[unit_start + 1:unit_end].strip()
                    spec = spec[:unit_start].strip()
            
            # Split category and subcategory
            parts = spec.split(" - ", 1)
            subcategory = parts[1] if len(parts) > 1 else ""
            category = parts[0]
                
            diff = Difference(
                category=category,
                subcategory=subcategory,
                unit=unit,
                values=values
            )
            # Only add if values are actually different
            if diff.has_differences():
                differences.append(diff)
        
        return cls(differences=differences)

    def add_difference(
        self,
        category: str,
        subcategory: str,
        unit: Optional[str],
        values: Dict[str, str]
    ) -> None:
        """Add a new difference if values are actually different."""
        diff = Difference(
            category=category,
            subcategory=subcategory,
            unit=unit,
            values=values
        )
        # Only add if values are actually different
        if diff.has_differences():
            self.differences.append(diff)

    def has_differences(self) -> bool:
        """Check if there are any differences."""
        return any(diff.has_differences() for diff in self.differences) 