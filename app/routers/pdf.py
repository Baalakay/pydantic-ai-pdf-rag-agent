from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List, Dict, Any
import os
from pydantic import BaseModel
import logging
from ..core import PDFProcessor
from ..models.vector import VectorEntry
from ..core.vector_store import VectorStore
from openai import OpenAI

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/pdf", tags=["pdf"])

class PDFResponse(BaseModel):
    """Response model for PDF operations."""
    filename: str
    page_count: int
    metadata: Dict[str, str]

def get_pdf_processor() -> PDFProcessor:
    """Dependency to get PDF processor instance."""
    storage_path = os.getenv("PDF_STORAGE_PATH", "uploads/pdfs")
    return PDFProcessor(storage_path)

async def get_vector_store() -> VectorStore:
    """Dependency to get vector store instance."""
    openai_client = OpenAI()
    return VectorStore(openai_client)

@router.post("/upload", response_model=PDFResponse)
async def upload_pdf(
    file: UploadFile = File(...),
    pdf_processor: PDFProcessor = Depends(get_pdf_processor),
    vector_store: VectorStore = Depends(get_vector_store)
) -> PDFResponse:
    """Upload and process a PDF file.
    Args:
        file: PDF file to upload
    Returns:
        PDFResponse with file info and metadata
    """
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="File must be a PDF")

    try:
        # Save the uploaded file
        filename = file.filename
        file_path = os.path.join(pdf_processor.storage_path, filename)
        with open(file_path, "wb") as pdf_file:
            content = await file.read()
            pdf_file.write(content)

        # Process the PDF
        document = pdf_processor.process_pdf(filename)

        # Add sections to vector store
        for section in document.sections:
            logger.info(f"Adding section to vector store: {section.content[:100]}...")
            await vector_store.add_entry(
                content=section.content,
                filename=section.filename,
                page_number=section.page_number
            )

        return PDFResponse(
            filename=document.filename,
            page_count=int(document.metadata["page_count"]),
            metadata=document.metadata
        )

    except Exception as e:
        logger.error(f"Error processing PDF upload: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

@router.get("/list", response_model=List[PDFResponse])
async def list_pdfs(
    pdf_processor: PDFProcessor = Depends(get_pdf_processor)
) -> List[PDFResponse]:
    """List all uploaded PDFs.
    Returns:
        List of PDFResponse objects
    """
    try:
        pdfs = []
        for filename in os.listdir(pdf_processor.storage_path):
            if filename.lower().endswith('.pdf'):
                document = pdf_processor.process_pdf(filename)
                pdfs.append(PDFResponse(
                    filename=document.filename,
                    page_count=int(document.metadata["page_count"]),
                    metadata=document.metadata
                ))
        return pdfs

    except Exception as e:
        logger.error(f"Error listing PDFs: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing PDFs")

@router.delete("/{filename}")
async def delete_pdf(
    filename: str,
    pdf_processor: PDFProcessor = Depends(get_pdf_processor)
) -> Dict[str, str]:
    """Delete a PDF file.
    Args:
        filename: Name of the PDF file to delete
    Returns:
        Message indicating success
    """
    try:
        file_path = os.path.join(pdf_processor.storage_path, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF not found")

        os.remove(file_path)
        return {"message": f"PDF {filename} deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Error deleting PDF")

@router.get("/vector-entries")
async def list_vector_entries(
    vector_store: VectorStore = Depends(get_vector_store)
) -> List[Dict[str, Any]]:
    """List all entries in the vector store."""
    try:
        entries = []
        for entry in vector_store.entries:
            entries.append({
                "content": entry.content[:200] + "..." if len(entry.content) > 200 else entry.content,
                "filename": entry.filename,
                "similarity_score": entry.similarity_score
            })
        return entries
    except Exception as e:
        logger.error(f"Error listing vector entries: {str(e)}")
        raise HTTPException(status_code=500, detail="Error listing vector entries")

@router.get("/download/{filename}")
async def download_pdf(
    filename: str,
    pdf_processor: PDFProcessor = Depends(get_pdf_processor)
) -> Any:
    """Download a PDF file.
    Args:
        filename: Name of the PDF file to download
    Returns:
        FileResponse containing the PDF
    """
    from fastapi.responses import FileResponse
    try:
        file_path = os.path.join(pdf_processor.storage_path, filename)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="PDF not found")

        return FileResponse(
            file_path,
            media_type="application/pdf",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading PDF")
