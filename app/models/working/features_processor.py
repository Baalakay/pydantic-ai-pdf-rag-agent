import os
from typing import List, Dict
from uuid import uuid4
import pdfplumber
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.models.features import FeatureSet

class FeaturesProcessor:
    """Processes PDF documents to extract features and advantages."""

    def __init__(self, storage_path: str):
        """Initialize the processor.

        Args:
            storage_path: Directory path where PDFs are stored
        """
        self.storage_path = storage_path
        os.makedirs(storage_path, exist_ok=True)

    def extract_features(self, pdf_path: str) -> FeatureSet:
        """Extract features and advantages from a PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            FeatureSet containing extracted features and advantages
        """
        bullet_points = []
        current_point = ""
        last_bullet_line = None

        with pdfplumber.open(pdf_path) as pdf:
            page = pdf.pages[0]
            text = page.extract_text()
            lines = text.split('\n')

            collecting_points = False
            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                if 'Features' in line or 'Advantages' in line:
                    collecting_points = True
                    continue

                if collecting_points:
                    if 'Electrical Specifications' in line or 'Magnetic Specifications' in line:
                        if current_point:
                            bullet_points.append(current_point.strip())
                        break

                    if '•' in line:
                        if current_point:
                            bullet_points.append(current_point.strip())
                            current_point = ""

                        # Split line by bullet points
                        parts = line.split('•')
                        for part in parts[1:]:  # Skip first empty part
                            if part.strip():
                                if current_point:
                                    bullet_points.append(current_point.strip())
                                current_point = part.strip()
                        last_bullet_line = i
                    elif collecting_points and line.strip():
                        # Check if this line is a continuation
                        if last_bullet_line is not None:
                            is_next_line = i == last_bullet_line + 1  # Next line after bullet point
                            is_short_word = len(line.split()) <= 2  # Short word
                            if is_next_line and is_short_word:
                                # Find the bullet point this belongs to
                                for j in range(len(bullet_points) - 1, -1, -1):
                                    if "Voltage Breakdown" in bullet_points[j]:
                                        bullet_points[j] += " " + line.strip()
                                        break
                                if current_point and "Voltage Breakdown" in current_point:
                                    current_point += " " + line.strip()
                            else:
                                if current_point:
                                    bullet_points.append(current_point.strip())
                                current_point = line.strip()

            # Add the last point if exists
            if current_point:
                bullet_points.append(current_point.strip())

            # Clean up bullet points
            cleaned_points = []
            seen = set()
            for point in bullet_points:
                if point not in seen and len(point.split()) > 1:
                    cleaned_points.append(point)
                    seen.add(point)
            bullet_points = cleaned_points

            # Classify points
            features = []
            advantages = []
            for i, point in enumerate(bullet_points, 1):
                if i <= 5 and i % 2 == 1:  # First three odd-numbered points
                    features.append(point)
                else:
                    advantages.append(point)

            return FeatureSet(
                id=uuid4(),
                features=features,
                advantages=advantages,
                source_file=os.path.basename(pdf_path),
                updated_at=None
            )

    def query_features(self, pdf_path: str, query_type: str = "all") -> Dict[str, List[str]]:
        """Query features or advantages from a PDF.

        Args:
            pdf_path: Path to the PDF file
            query_type: Type of query - "features", "advantages", or "all"

        Returns:
            Dictionary containing requested features and/or advantages
        """
        feature_set = self.extract_features(pdf_path)

        if query_type == "features":
            return {"features": feature_set.features}
        elif query_type == "advantages":
            return {"advantages": feature_set.advantages}
        else:
            return {
                "features": feature_set.features,
                "advantages": feature_set.advantages
            }

def test_features_processor() -> None:
    """Test function to demonstrate features extraction for all PDFs."""
    processor = FeaturesProcessor("uploads/pdfs")

    # Get all PDF files in the directory
    pdf_files = [f for f in os.listdir("uploads/pdfs") if f.endswith(".pdf")]

    for i, pdf_file in enumerate(pdf_files, 1):
        pdf_path = os.path.join("uploads/pdfs", pdf_file)
        results = processor.query_features(pdf_path)

        print(f"\nProcessing PDF {i}/{len(pdf_files)}: {pdf_file}")
        print("\nFeatures:")
        for feature in results["features"]:
            print(f"- {feature}")

        print("\nAdvantages:")
        for advantage in results["advantages"]:
            print(f"- {advantage}")

        print("\n" + "=" * 80 + "\n")

        if i < len(pdf_files):
            input("Press Enter to process the next PDF...")

if __name__ == "__main__":
    test_features_processor()
