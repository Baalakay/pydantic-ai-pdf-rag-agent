from typing import List, Dict
import os
import pdfplumber
import re
from app.models.pdf import PDFSection, PDFDocument
from app.core.parsers import PDFSectionParser


class PDFProcessor:
    """Processes PDF files to extract structured content."""

    def __init__(self, storage_path: str = "uploads/pdfs"):
        self.storage_path = storage_path
        self.parser = PDFSectionParser()
        self.section_patterns = {
            'features': r'Features',
            'advantages': r'Advantages',
            'electrical': r'Electrical\s+Specifications',
            'magnetic': r'Magnetic\s+Specifications',
            'physical': r'Physical/Operational\s+Specifications',
            'notes': r'Notes'
        }

    def _extract_sections(self, text: str) -> Dict[str, List[str]]:
        """Extract raw text sections from PDF content."""
        sections: Dict[str, List[str]] = {
            'features': [],
            'advantages': [],
            'electrical': [],
            'magnetic': [],
            'physical': [],
            'notes': []
        }
        
        current_section = None
        current_text: List[str] = []
        
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Check for section headers
            for section, pattern in self.section_patterns.items():
                if re.match(pattern, line, re.IGNORECASE):
                    if current_section:
                        sections[current_section].extend(current_text)
                    current_section = section
                    current_text = []
                    break
            else:
                if current_section:
                    current_text.append(line)
                    
        # Add remaining text
        if current_section:
            sections[current_section].extend(current_text)
            
        return sections

    def process_pdf(self, filename: str) -> PDFDocument:
        """Process a PDF file and return structured content."""
        file_path = os.path.join(self.storage_path, filename)
        
        # Extract text from PDF
        with pdfplumber.open(file_path) as pdf:
            text = '\n'.join(page.extract_text() for page in pdf.pages)
            
        # Extract raw sections
        raw_sections = self._extract_sections(text)
        
        # Parse sections into structured format
        pdf_sections: List[PDFSection] = []
        
        # Features
        if raw_sections['features']:
            features_content = self.parser.parse_features_advantages(
                raw_sections['features']
            )
            pdf_sections.append(PDFSection(
                section_type='features',
                content=features_content
            ))
            
        # Advantages
        if raw_sections['advantages']:
            advantages_content = self.parser.parse_features_advantages(
                raw_sections['advantages']
            )
            pdf_sections.append(PDFSection(
                section_type='advantages',
                content=advantages_content
            ))
            
        # Electrical Specifications
        if raw_sections['electrical']:
            electrical_content = self.parser.parse_electrical(
                raw_sections['electrical']
            )
            pdf_sections.append(PDFSection(
                section_type='electrical',
                content=electrical_content
            ))
            
        # Magnetic Specifications
        if raw_sections['magnetic']:
            magnetic_content = self.parser.parse_magnetic(
                raw_sections['magnetic']
            )
            pdf_sections.append(PDFSection(
                section_type='magnetic',
                content=magnetic_content
            ))
            
        # Physical Specifications
        if raw_sections['physical']:
            physical_content = self.parser.parse_physical(
                raw_sections['physical']
            )
            pdf_sections.append(PDFSection(
                section_type='physical',
                content=physical_content
            ))
            
        # Notes
        if raw_sections['notes']:
            notes_content = self.parser.parse_notes(raw_sections['notes'])
            pdf_sections.append(PDFSection(
                section_type='notes',
                content=notes_content
            ))
            
        return PDFDocument(
            filename=filename,
            sections=pdf_sections
        )
