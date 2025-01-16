from typing import List, Optional, Union
from pydantic import BaseModel, Field


class SpecValue(BaseModel):
    """Represents a specification value with optional unit."""
    value: float
    unit: Optional[str] = None


class ElectricalSpecs(BaseModel):
    """Electrical specifications structured by category."""
    power: dict[str, SpecValue] = Field(default_factory=dict)
    voltage: dict[str, SpecValue] = Field(default_factory=dict)
    current: dict[str, SpecValue] = Field(default_factory=dict)
    resistance: dict[str, SpecValue] = Field(default_factory=dict)
    capacitance: dict[str, SpecValue] = Field(default_factory=dict)


class MagneticSpecs(BaseModel):
    """Magnetic specifications structured by category."""
    operate_point: dict[str, SpecValue] = Field(default_factory=dict)
    release_point: dict[str, SpecValue] = Field(default_factory=dict)
    pull_in_range: dict[str, SpecValue] = Field(default_factory=dict)
    drop_out_range: dict[str, SpecValue] = Field(default_factory=dict)


class PhysicalSpecs(BaseModel):
    """Physical and operational specifications."""
    dimensions: dict[str, SpecValue] = Field(default_factory=dict)
    temperature: dict[str, SpecValue] = Field(default_factory=dict)
    timing: dict[str, SpecValue] = Field(default_factory=dict)
    material: dict[str, str] = Field(default_factory=dict)


# Define possible content types
SectionContent = Union[
    ElectricalSpecs,
    MagneticSpecs,
    PhysicalSpecs,
    List[str],  # For features and advantages
    str,  # For notes
]


class PDFSection(BaseModel):
    """Represents a section in a PDF document."""
    section_type: str = Field(
        ...,
        description="Type of section (features, advantages, etc)"
    )
    content: SectionContent = Field(
        ...,
        description="Content of the section"
    )


class PDFDocument(BaseModel):
    """Represents a processed PDF document."""
    filename: str = Field(..., description="Name of the PDF file")
    sections: List[PDFSection] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    diagram_path: Optional[str] = None
    page_count: int = Field(default=0)
