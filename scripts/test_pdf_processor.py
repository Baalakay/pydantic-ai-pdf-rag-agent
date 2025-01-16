#!/usr/bin/env python3
import os
import sys

# Add project root to Python path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
    
from app.core.pdf_processor import PDFProcessor  # noqa: E402


def process_pdf(filename: str) -> None:
    """Process a single PDF and output its structured content."""
    processor = PDFProcessor()
    processor.process_pdf(os.path.join("uploads/pdfs", filename))


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
    
    process_pdf(filename)


if __name__ == "__main__":
    main() 