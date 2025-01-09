import os
from typing import Dict, List, Any
from pypdf import PdfReader
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class PDFSection(BaseModel):
    """Represents a section of text from a PDF."""
    content: str
    page_number: int
    section_number: int
    filename: str

class PDFDocument(BaseModel):
    """Represents a processed PDF document."""
    filename: str
    sections: List[PDFSection]
    metadata: Dict[str, str]

class PDFProcessor:
    """Handles PDF document processing and text extraction."""
    def __init__(self, storage_path: str):
        """Initialize the PDF processor.
        Args:
            storage_path: Directory path where PDFs are stored
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def process_pdf(self, filename: str) -> PDFDocument:
        """Process a PDF file and extract its contents.
        Args:
            filename: Name of the PDF file to process
        Returns:
            PDFDocument containing extracted text and metadata
        """
        filepath = os.path.join(self.storage_path, filename)
        logger.info(f"Processing PDF: {filepath}")
        try:
            reader = PdfReader(filepath)
            sections: List[PDFSection] = []

            # Extract text from each page
            for page_num, page in enumerate(reader.pages, 1):
                text = page.extract_text()

                # Clean and normalize the text
                text = text.replace('\x00', ' ')  # Remove null bytes
                text = ' '.join(text.split())  # Normalize whitespace

                # Add context about which document this is from
                context = f"From document: {filename} (Page {page_num})\n\n"

                # Create a single section per page with context
                if text.strip():
                    sections.append(PDFSection(
                        content=context + text,
                        page_number=page_num,
                        section_number=1,
                        filename=filename
                    ))

            # Extract metadata safely
            metadata_info: Dict[str, Any] = reader.metadata or {}
            metadata = {
                "title": str(metadata_info.get("/Title", "")),
                "author": str(metadata_info.get("/Author", "")),
                "creation_date": str(metadata_info.get("/CreationDate", "")),
                "page_count": str(len(reader.pages))
            }

            return PDFDocument(
                filename=filename,
                sections=sections,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Error processing PDF {filename}: {str(e)}", exc_info=True)
            raise
