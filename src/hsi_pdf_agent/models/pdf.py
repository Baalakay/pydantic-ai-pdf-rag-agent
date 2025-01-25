"""PDF data models."""
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, model_validator, ConfigDict, computed_field
from pathlib import Path
import re

from hsi_pdf_agent.core.transformers import TransformedSpecValue, SpecTransformer
from hsi_pdf_agent.core.config import get_settings


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
    model_name: str
    sections: Dict[str, SectionData]
    notes: Optional[Dict[str, str]] = None
    diagram_path: Optional[str] = None

    @computed_field
    @property
    def model_number(self) -> str:
        """Extract numeric model number from full model name (e.g., '520' from 'HSR-520R')."""
        return self.model_name.split('-')[1].rstrip('RFW')

    model_config = ConfigDict(
        json_schema_extra={
            "required": ["model_name", "sections"],
            "properties": {
                "model_name": {},
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
    ) -> Optional[tuple[Path, str]]:
        """Find a PDF file based on a model keyword.
        
        Returns:
            Optional tuple of (pdf_path, model_name) where model_name is in HSR-XXXR format
        """
        if pdf_dir is None:
            settings = get_settings()
            pdf_dir = settings.PDF_DIR

        if not isinstance(pdf_dir, Path):
            raise TypeError("PDF directory must be a Path object")

        if not pdf_dir.exists():
            return None

        clean_keyword = (
            model_keyword.upper()
            .replace('HSR-', '')
            .replace('HSR', '')
        )

        for pdf_path in pdf_dir.glob("*.pdf"):
            match = re.search(
                r'HSR-(\d+[RFW]?)-',
                pdf_path.name,
                re.IGNORECASE
            )
            if match:
                model_number = match.group(1)
                if (clean_keyword in model_number or
                        model_number in clean_keyword):
                    full_model = f"HSR-{model_number}"
                    return pdf_path, full_model
        return None
