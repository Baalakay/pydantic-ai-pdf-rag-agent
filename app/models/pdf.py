from typing import Dict, List, Optional, Union
from pydantic import BaseModel, model_validator
from .transformers import TransformedSpecValue, SpecTransformer


class SpecValue(BaseModel):
    """Represents a specification value with optional unit."""
    unit: Optional[str] = None
    value: Union[str, float, int]
    transformed: Optional[TransformedSpecValue] = None
    
    @model_validator(mode='after')
    def transform_value(self) -> 'SpecValue':
        """Transform the value after validation."""
        self.transformed = SpecTransformer.transform_spec(
            unit=self.unit,
            value=str(self.value)
        )
        return self


class CategorySpec(BaseModel):
    """Represents specifications for a category."""
    subcategories: Dict[str, Dict[str, SpecValue]]


class SectionData(BaseModel):
    """Represents data for a section."""
    categories: Dict[str, CategorySpec]


class PDFData(BaseModel):
    """Model for storing structured data extracted from a PDF."""
    sections: Dict[str, SectionData]
    features_advantages: Dict[str, List[str]] | None = None
    notes: Dict[str, str] | None = None
    
    model_config = {
        "json_schema_extra": {
            "required": ["sections"],
            "properties": {
                "sections": {},
                "features_advantages": {},
                "notes": {}
            }
        },
        "json_schema_serialization_defaults": {
            "include": ["sections", "features_advantages", "notes"]
        }
    }
