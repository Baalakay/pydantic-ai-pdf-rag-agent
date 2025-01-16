from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field


class SpecDict(BaseModel):
    """Represents a raw specification value with optional unit."""
    unit: Optional[str] = None
    value: str


# Define possible content types
SectionContent = Union[
    Dict[str, List[str]],  # For features_advantages
    Dict[str, Dict[str, SpecDict]],  # For specifications
    str,  # For notes
]


class PDFSection(BaseModel):
    """Represents a section in a PDF document."""
    section_type: str = Field(
        ...,
        description="Type of section (features_advantages, electrical, etc)"
    )
    content: SectionContent = Field(
        ...,
        description="Content of the section"
    )


class PDFDocument(BaseModel):
    """Represents a processed PDF document."""
    filename: str
    sections: List[PDFSection]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    diagram_path: Optional[str] = None
    page_count: int
