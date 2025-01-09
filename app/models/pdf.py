from typing import List
from pydantic import Field
from .base import BaseDocument

class PDFSection(BaseDocument):
    """Model for a section of text from a PDF."""
    content: str = Field(..., description="The text content of the section")
    page_number: int = Field(..., description="Page number in the PDF")
    section_number: int = Field(..., description="Section number in the page")

class PDFDocument(BaseDocument):
    """Model for a PDF document."""
    filename: str = Field(..., description="Original filename of the PDF")
    file_path: str = Field(..., description="Path where the PDF is stored")
    page_count: int = Field(..., description="Number of pages in the PDF")
    sections: List[PDFSection] = Field(
        default_factory=list,
        description="Extracted sections from the PDF"
    )
    status: str = Field(
        default="pending",
        description="Processing status: pending, processing, completed, failed"
    )
