#!/usr/bin/env python3
import os
import sys
import pdfplumber

# Add project root to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    
from app.pdf_reader import extract_sections  # noqa: E402


def examine_pdf(filename: str) -> None:
    """Show raw text and extracted sections from a PDF."""
    filepath = os.path.join("uploads/pdfs", filename)
    
    # Show raw text from PDF
    print("\nRaw text from PDF:")
    print("=" * 80)
    with pdfplumber.open(filepath) as pdf:
        text = pdf.pages[0].extract_text()
        print(text)
    print("=" * 80)
    
    # Show extracted sections
    print("\nExtracted sections:")
    print("=" * 80)
    sections = extract_sections(filepath)
    for section, content in sections.items():
        print(f"\n{section.upper()}:")
        for line in content:
            print(f"  {line}")
    print("=" * 80)


def main() -> None:
    """Process PDFs in the uploads/pdfs directory."""
    pdfs_dir = "uploads/pdfs"
    pdf_files = [f for f in os.listdir(pdfs_dir) if f.endswith('.pdf')]
    
    if not pdf_files:
        print("No PDFs found in uploads/pdfs directory")
        return
        
    print("\nAvailable PDFs:")
    for i, filename in enumerate(pdf_files, 1):
        print(f"{i}. {filename}")
    
    prompt = "\nSelect PDF number (or press Enter for first): "
    while True:
        try:
            choice = input(prompt).strip()
            if not choice:
                filename = pdf_files[0]
                break
            
            idx = int(choice) - 1
            if 0 <= idx < len(pdf_files):
                filename = pdf_files[idx]
                break
            else:
                print("Invalid selection. Please try again.")
        except ValueError:
            print("Please enter a valid number.")
    
    examine_pdf(filename)


if __name__ == "__main__":
    main() 