"""Script to compare model specifications."""
from app.models import ComparisonResult


def main() -> None:
    """Run raw comparison to verify output."""
    result = ComparisonResult.from_model_names(["520R", "630"])
    print(result)


if __name__ == "__main__":
    main()
