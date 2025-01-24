#!/usr/bin/env python3
"""Script to test PDF processing."""
import json
from ..core.process_pdf import PDFProcessor


def main() -> None:
    """Run the test."""
    processor = PDFProcessor()

    # Test with model number
    model = "520"
    print(f"\nProcessing PDF for model {model}...")

    try:
        result = processor.process_pdf(model)
        # Convert to dict for pretty printing
        result_dict = result.model_dump()
        print(json.dumps(result_dict, indent=2))
    except Exception as e:
        print(f"Error processing PDF: {e}")


if __name__ == "__main__":
    main()
