"""Script to compare model specifications."""
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)
import asyncio
from backend.src.app.core.process_compare import ComparisonProcessor


async def main(model_names):
    """Run the comparison and print the raw result."""
    service = ComparisonProcessor()
    result = await service.compare_models(model_names)
    print(str(result))


if __name__ == "__main__":
    asyncio.run(main(["980", "190R", "520", "1016R"]))
