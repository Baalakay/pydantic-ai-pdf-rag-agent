import pdfplumber
from typing import List, Tuple

def extract_sections(pdf_path: str) -> Tuple[List[str], List[str]]:
    """Extract Features and Advantages sections from the PDF."""
    features = []
    advantages = []
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

    # Classify points using 1-based indexing
    for i, point in enumerate(bullet_points, 1):
        if i <= 5 and i % 2 == 1:  # First three odd-numbered points (1, 3, 5)
            features.append(point)
        else:
            advantages.append(point)

    print(f"\nClassified Results for {pdf_path.split('/')[-1]}:\n")
    print("Extracted Features:")
    for feature in features:
        print(f"- {feature}")

    print("\nExtracted Advantages:")
    for advantage in advantages:
        print(f"- {advantage}")

    print("\n" + "=" * 80 + "\n")
    return features, advantages

def test_all_pdfs() -> None:
    pdf_path = "uploads/pdfs/b7947df6-147b-4bae-92f8-bfa9bf6c5b09_HSR-520R-Series-Rev-K.pdf"
    extract_sections(pdf_path)

if __name__ == "__main__":
    test_all_pdfs()
