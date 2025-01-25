#!/usr/bin/env python3
"""Script to compare model specifications."""
import asyncio
from hsi_pdf_agent.core.process_compare import ComparisonProcessor


async def main():
    processor = ComparisonProcessor()
    try:
        result = await processor.compare_models(["520", "980"])
        print(result)
    except Exception as e:
        raise


if __name__ == "__main__":
    asyncio.run(main())
