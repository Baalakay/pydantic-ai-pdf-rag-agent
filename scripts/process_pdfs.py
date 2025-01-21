#!/usr/bin/env python3
from pathlib import Path
import httpx
import asyncio
from typing import List
from app.core.config import get_settings


async def process_pdfs() -> None:
    """Process all PDFs in the data/pdfs directory."""
    settings = get_settings()
    pdf_files: List[Path] = list(settings.PDF_DIR.glob("*.pdf"))

    if not pdf_files:
        print("No PDF files found in directory.")
        return

    async with httpx.AsyncClient() as client:
        for pdf_path in pdf_files:
            print(f"Processing {pdf_path.name}...")

            # Create form data with the PDF file
            with pdf_path.open('rb') as file:
                form_data = {'file': file}
                try:
                    response = await client.post(
                        "http://localhost:8000/pdf/upload",
                        files=form_data
                    )
                    if response.status_code == 200:
                        print(f"✓ Successfully processed {pdf_path.name}")
                    else:
                        print(f"✗ Error processing {pdf_path.name}: {response.text}")
                except Exception as e:
                    print(f"✗ Error processing {pdf_path.name}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(process_pdfs())
