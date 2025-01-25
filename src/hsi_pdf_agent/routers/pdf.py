from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import List, Dict, Any, cast
from pydantic import BaseModel
import logging
from openai import OpenAI
from pathlib import Path

from hsi_pdf_agent.core.process_pdf import PDFProcessor
from hsi_pdf_agent.core.vector_store import VectorStore
from hsi_pdf_agent.core.config import get_settings


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/pdf", tags=["pdf"])


class PDFResponse(BaseModel):
    """Response model for PDF operations."""
    filename: str
    page_count: int
    metadata: Dict[str, Any]


def get_pdf_processor() -> PDFProcessor:
    """Dependency to get PDF processor instance."""
    settings = get_settings()
    processor = PDFProcessor()
    pdf_dir = cast(Path, settings.PDF_DIR)
    if not pdf_dir.exists():
        pdf_dir.mkdir(parents=True, exist_ok=True)
    processor.current_file = pdf_dir
    return processor


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
        if not pdf_processor.current_file or not isinstance(pdf_processor.current_file, Path):
            raise HTTPException(status_code=500, detail="PDF directory not configured")

        file_path = pdf_processor.current_file / file.filename
        with open(file_path, "wb") as pdf_file:
            content = await file.read()
            pdf_file.write(content)

        # Process the PDF
        document = pdf_processor.process_pdf(str(file_path))

        # Add sections to vector store
        for section_name, section_data in document.sections.items():
            logger.info(f"Adding section to vector store: {section_name}...")
            await vector_store.add_entry(
                content=str(section_data),
                filename=file.filename,
                page_number=1  # TODO: Add actual page number tracking
            )

        return PDFResponse(
            filename=file.filename,
            page_count=len(document.sections),
            metadata={"sections": [str(s) for s in document.sections.keys()]}
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
        if not pdf_processor.current_file or not isinstance(pdf_processor.current_file, Path):
            raise HTTPException(status_code=500, detail="PDF directory not configured")

        pdfs = []
        for file_path in pdf_processor.current_file.glob("*.pdf"):
            document = pdf_processor.process_pdf(str(file_path))
            pdfs.append(PDFResponse(
                filename=file_path.name,
                page_count=len(document.sections),
                metadata={"sections": [str(s) for s in document.sections.keys()]}
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
        if not pdf_processor.current_file or not isinstance(pdf_processor.current_file, Path):
            raise HTTPException(status_code=500, detail="PDF directory not configured")

        file_path = pdf_processor.current_file / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="PDF not found")

        file_path.unlink()
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
) -> FileResponse:
    """Download a PDF file.
    Args:
        filename: Name of the PDF file to download
    Returns:
        FileResponse containing the PDF
    """
    try:
        if not pdf_processor.current_file or not isinstance(pdf_processor.current_file, Path):
            raise HTTPException(status_code=500, detail="PDF directory not configured")

        file_path = pdf_processor.current_file / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="PDF not found")

        return FileResponse(
            str(file_path),
            media_type="application/pdf",
            filename=filename
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail="Error downloading PDF")
