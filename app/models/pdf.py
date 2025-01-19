from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, model_validator, ConfigDict
from pathlib import Path
import re
import os
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
        
    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Override model_dump to exclude transformed field."""
        kwargs['exclude'] = {'transformed'} | kwargs.get('exclude', set())
        return super().model_dump(*args, **kwargs)
    
    model_config = ConfigDict(
        json_schema_extra={
            "exclude": ["transformed"]
        }
    )


class CategorySpec(BaseModel):
    """Represents specifications for a category."""
    subcategories: Dict[str, SpecValue]


class SectionData(BaseModel):
    """Represents data for a section."""
    categories: Dict[str, CategorySpec]


class FeaturesAdvantages(BaseModel):
    """Model for features and advantages."""
    features: List[str]
    advantages: List[str]


class PDFData(BaseModel):
    """Model for storing structured data extracted from a PDF."""
    sections: Dict[str, SectionData]
    notes: Optional[Dict[str, str]] = None
    diagram_path: Optional[str] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "required": ["sections"],
            "properties": {
                "sections": {},
                "notes": {},
                "diagram_path": {}
            }
        }
    )


class PDFLocator(BaseModel):
    """Model for locating PDF files based on model keywords."""
    model_config = ConfigDict(frozen=True, extra="forbid")

    @classmethod
    def find_pdf_by_model(
        cls,
        model_keyword: str,
        pdf_dir: Optional[Path] = None
    ) -> Optional[Path]:
        """Find a PDF file based on a model keyword."""
        if pdf_dir is None:
            pdf_dir = Path("uploads/pdfs")
            
        clean_keyword = (
            model_keyword.upper()
            .replace('HSR-', '')
            .replace('HSR', '')
        )

        for filename in os.listdir(pdf_dir):
            if filename.endswith('.pdf'):
                match = re.search(
                    r'HSR-(\d+[RFW]?)-',
                    filename,
                    re.IGNORECASE
                )
                if match:
                    model_number = match.group(1)
                    if (clean_keyword in model_number or
                            model_number in clean_keyword):
                        return pdf_dir / filename
        return None
