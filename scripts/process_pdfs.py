#!/usr/bin/env python3
import os
import httpx
import asyncio

async def process_pdfs() -> None:
    """Process all PDFs in the uploads/pdfs directory."""
    pdf_dir = "uploads/pdfs"
    pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]

    async with httpx.AsyncClient() as client:
        for pdf_file in pdf_files:
            print(f"Processing {pdf_file}...")

            # Create form data with the PDF file
            form_data = {'file': open(os.path.join(pdf_dir, pdf_file), 'rb')}

            try:
                response = await client.post(
                    "http://localhost:8000/pdf/upload",
                    files=form_data
                )
                if response.status_code == 200:
                    print(f"✓ Successfully processed {pdf_file}")
                else:
                    print(f"✗ Error processing {pdf_file}: {response.text}")
            except Exception as e:
                print(f"✗ Error processing {pdf_file}: {str(e)}")
            finally:
                # Close the file handle
                form_data['file'].close()

if __name__ == "__main__":
    asyncio.run(process_pdfs())
