"""Script to compare model specifications."""
import asyncio
from app.core.comparison.service import ComparisonService


async def main() -> None:
    """Run raw comparison to verify output."""
    service = ComparisonService()
    result = await service.compare_models(["980", "190R"])
    print(str(result))


if __name__ == "__main__":
    asyncio.run(main())
