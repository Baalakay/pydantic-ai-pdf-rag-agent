#!/usr/bin/env python3
import os
import sys

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from app.models import PDFDocument
from app.pdf_reader import extract_sections
from app.core.pdf_processor import PDFProcessor


def format_pdf_reader_output(sections: dict, indent: int = 0) -> str:
    """Format the output from pdf_reader.py"""
    output = []
    for section_type, content in sections.items():
        if not content:
            continue
        output.append("=== " + section_type.upper() + " ===\n")
        if isinstance(content, list):
            output.append("\n".join(content) + "\n")
        else:
            output.append(content.strip() + "\n")
        output.append("")
    return "\n".join(output)


def format_processor_output(doc: PDFDocument, indent: int = 0) -> str:
    """Format the output from PDFProcessor"""
    output = []
    for section in doc.sections:
        output.append("=== " + section.section_type.upper() + " ===\n")
        output.append(section.content.strip() + "\n")
        output.append("")
    return "\n".join(output)


def main() -> None:
    """Compare output from both PDF processors."""
    # List available PDFs
    print("Available PDFs:")
    for filename in os.listdir("uploads/pdfs"):
        if filename.endswith(".pdf"):
            print(f"- {filename}")
    
    # Get filename from user or use default
    print("\nEnter PDF filename (or press Enter for first PDF): ", end="")
    filename = input().strip()
    if not filename:
        pdfs = [f for f in os.listdir("uploads/pdfs") if f.endswith(".pdf")]
        if not pdfs:
            print("No PDFs found in uploads/pdfs directory")
            return
        filename = pdfs[0]
    
    filepath = os.path.join("uploads/pdfs", filename)
    print(f"\nProcessing {filename}...")
    
    print("\n" + "="*80)
    print("Output from pdf_reader.py:")
    print("="*80)
    try:
        sections = extract_sections(filepath)
        print(format_pdf_reader_output(sections))
    except Exception as e:
        print(f"Error from pdf_reader: {str(e)}")
    
    print("\n" + "="*80)
    print("Output from pdf_processor.py:")
    print("="*80)
    try:
        processor = PDFProcessor("uploads/pdfs")
        doc = processor.process_pdf(filename)
        print(format_processor_output(doc))
    except Exception as e:
        print(f"Error from pdf_processor: {str(e)}")


if __name__ == "__main__":
    main() 