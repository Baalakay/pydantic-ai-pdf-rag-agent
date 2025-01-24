#!/usr/bin/env python3
"""Script to compare model specifications."""
import logging
import asyncio
from src.app.core.process_compare import ComparisonProcessor


# Disable verbose logging from dependencies and specific modules
logging.getLogger("src.app.core.process_pdf").setLevel(logging.WARNING)
logging.getLogger("pdfminer").setLevel(logging.WARNING)
logging.getLogger("pdfplumber").setLevel(logging.WARNING)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting PDF comparison test")
    
    # Initialize processor
    processor = ComparisonProcessor()
    logger.info("ComparisonProcessor initialized")
    
    # Use existing PDFs from data directory
    model1 = "520"
    model2 = "980"
    logger.info(f"Processing PDFs for models:\n  1: {model1}\n  2: {model2}")
    
    # Process PDFs
    try:
        result = await processor.compare_models([model1, model2])
        logger.info(f"Comparison result: {result}")
    except Exception as e:
        logger.error(f"Error during processing: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
