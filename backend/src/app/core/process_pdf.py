"""Service for processing PDF files."""
from typing import Dict, List, Optional
from pathlib import Path
import pdfplumber
import fitz  # type: ignore  # PyMuPDF
from backend.src.app.models.pdf import (
    PDFData, SectionData, CategorySpec, SpecValue
)
from backend.src.app.core.config import get_settings
import re


class PDFProcessor:
    def __init__(self) -> None:
        self.current_file: Optional[Path] = None
        self.text_sections = ['features', 'advantages', 'notes']
        self.section_patterns = {
            'electrical': 'electrical specifications',
            'magnetic': 'magnetic specifications',
            'physical': (
                'physical/operational specifications'
            )
        }
        self.section_order = ['electrical', 'magnetic', 'physical']

    def _extract_text(self, filename: str) -> str:
        """Extract text from the first page of a PDF file."""
        path = Path(filename)
        self.current_file = path
        with pdfplumber.open(path) as pdf:
            first_page = pdf.pages[0]
            return first_page.extract_text()

    def _parse_features_advantages(
        self,
        text: str,
        tables: List[List[List[str]]]
    ) -> Optional[Dict[str, SectionData]]:
        """Extract features and advantages using bounding boxes."""
        if not self.current_file:
            return None

        features: List[str] = []
        advantages: List[str] = []

        with pdfplumber.open(self.current_file) as pdf:
            page = pdf.pages[0]

            # Extract features from left box
            feat_box = (0, 130, 295, 210)
            feat_area = page.within_bbox(feat_box)
            feat_text = feat_area.extract_text()
            if feat_text:
                features = []
                for line in feat_text.split('\n'):
                    line = line.strip()
                    if line and line.lower() != 'features':
                        features.append(line)

            # Extract advantages from right box
            adv_box = (300, 130, 610, 210)
            adv_area = page.within_bbox(adv_box)
            adv_text = adv_area.extract_text()
            if adv_text:
                advantages = []
                for line in adv_text.split('\n'):
                    line = line.strip()
                    if line and line.lower() != 'advantages':
                        advantages.append(line)

        if features or advantages:
            return {
                'Features_And_Advantages': SectionData(
                    categories={
                        'Features': CategorySpec(
                            subcategories={
                                '': SpecValue(
                                    unit=None,
                                    value='\n'.join(features)
                                )
                            }
                        ),
                        'Advantages': CategorySpec(
                            subcategories={
                                '': SpecValue(
                                    unit=None,
                                    value='\n'.join(advantages)
                                )
                            }
                        )
                    }
                )
            }
        return None

    def _extract_tables(self, text: str) -> List[List[List[str]]]:
        """Extract tables from the first page of a PDF file."""
        if not self.current_file:
            return []
        with pdfplumber.open(self.current_file) as pdf:
            first_page = pdf.pages[0]
            tables = first_page.extract_tables()
            # Convert None values to empty strings
            return [
                [[str(cell) if cell else '' for cell in row] for row in table]
                for table in tables
            ]

    def _parse_table_to_specs(
        self,
        table: List[List[str]]
    ) -> Dict[str, Dict[str, SpecValue]]:
        """Parse a table into specifications."""
        if not table:  # Empty table
            return {}

        # Clean first row
        first_row = [
            str(col).strip() if col else "" for col in table[0]
        ]

        # Skip features/advantages table
        if (len(first_row) == 2 and
                "Features" in first_row[0] and
                "Advantages" in first_row[1]):
            return {}

        specs: Dict[str, Dict[str, SpecValue]] = {}
        current_category: Optional[str] = None

        # Check if first row is data
        is_first_row_data = (
            len(first_row) >= 3 and  # At least category, unit, value columns
            first_row[0] and  # Must have a category
            any(first_row[-2:])  # Must have either unit or value
        )

        # Process rows
        rows_to_process = table if is_first_row_data else table[1:]

        for row in rows_to_process:
            try:
                # Clean row data
                row_data = [
                    str(cell).strip() if cell else "" for cell in row
                ]

                if not any(row_data):  # Skip empty rows
                    continue

                # Get category and subcategory
                category = row_data[0] if row_data[0] else current_category
                subcategory = (
                    row_data[1] if len(row_data) > 1 and row_data[1] else ""
                )

                # Handle empty first column
                if not category and subcategory:
                    category = current_category

                if category and isinstance(category, str):
                    current_category = category
                    if category not in specs:
                        specs[category] = {}

                # Get unit and value
                if len(row_data) > 2:
                    unit = None
                    value = None

                    if len(row_data) > 3:
                        unit = row_data[2].strip() if row_data[2] else ""
                        value = row_data[3].strip() if row_data[3] else ""
                    else:
                        unit = ""
                        value = row_data[2].strip() if row_data[2] else ""

                    if value and category:
                        spec_value = SpecValue(unit=unit, value=value)
                        if subcategory:
                            specs[category][subcategory] = spec_value
                        else:
                            specs[category][""] = spec_value

            except (ValueError, IndexError) as e:
                err_msg = f"Error parsing row {row_data}: {str(e)}"
                print(err_msg)
                continue

        return specs

    def _determine_section_type(
        self,
        text: str,
        table_start_index: int
    ) -> str:
        """Find the section name that precedes this table position."""
        lines = text.split('\n')
        lines = [line.strip() for line in lines]

        # Find section headers and positions
        section_positions = []
        for i, line in enumerate(lines):
            if "Specifications" in line:
                section_positions.append((line.strip(), i))

        section_positions.sort(key=lambda x: x[1])

        # Default to last section if can't determine
        if not section_positions:
            return ""
        section_name = section_positions[-1][0]

        # Find section header that precedes table
        for i, (name, pos) in enumerate(section_positions):
            next_pos = (
                section_positions[i + 1][1]
                if i + 1 < len(section_positions)
                else len(lines)
            )

            if pos <= table_start_index < next_pos:
                section_name = name
                break

        return section_name

    def _extract_notes(self, text: str) -> List[str]:
        """Extract notes from the text."""
        notes = []
        collecting_notes = False
        current_note = ""

        lines = text.split('\n')
        for line in lines:
            line = line.strip()

            # Start collecting notes when we see the Notes header
            if 'Notes:' in line:
                collecting_notes = True
                # Don't include the header itself
                line = line.replace('Notes:', '').strip()

            if collecting_notes and line:
                # Handle bullet points
                if '•' in line:
                    if current_note:
                        notes.append(current_note)
                    current_note = line.strip()
                elif current_note:
                    current_note += ' ' + line
                else:
                    current_note = line

        # Add the last note if any
        if current_note:
            notes.append(current_note)

        return notes

    def _extract_model_name(self, filename: str) -> str:
        """Extract the model name from the PDF content.

        Args:
            filename: Name of the PDF file (used as fallback)

        Returns:
            str: Model name (e.g., '100R') or empty string if not found
        """
        if not self.current_file:
            return ""

        # First try to extract from PDF content
        with pdfplumber.open(self.current_file) as pdf:
            first_page = pdf.pages[0]
            text = first_page.extract_text()

            # Look for HSR- pattern in the text
            lines = text.split('\n')
            for line in lines:
                if 'HSR-' in line.upper():
                    # Extract HSR-XXXR/F/W pattern
                    parts = line.split()
                    for part in parts:
                        if 'HSR-' in part.upper():
                            # Extract just the model number (e.g., HSR-100R)
                            match = re.search(r'HSR-(\d+[RFW]?)', part, re.IGNORECASE)
                            if match:
                                # Return just the number and optional suffix
                                return match.group(1).upper()

        # Fallback: Try to extract from filename
        if filename:
            match = re.search(r'HSR-(\d+[RFW]?)', filename, re.IGNORECASE)
            if match:
                return match.group(1).upper()

        return ""

    def _format_section_name(self, name: str) -> str:
        """Format section name.

        Replaces non-alphanumeric chars with underscores.
        """
        # Replace non-alphanumeric chars with underscore
        formatted = ''.join(
            '_' if not c.isalnum() else c
            for c in name
        )
        # Remove duplicate underscores if any
        while '__' in formatted:
            formatted = formatted.replace('__', '_')
        # Remove leading/trailing underscores and convert to title case
        return formatted.strip('_').title()

    def _extract_model_diagram(self, output_dir: Optional[Path] = None) -> Optional[str]:
        """Extract the model diagram image from the PDF.

        Args:
            output_dir: Directory to save the diagram image. If None, uses settings.DIAGRAMS_DIR

        Returns:
            Optional[str]: Path to the saved image if successful, None otherwise
        """
        if not self.current_file:
            return None

        # Get output directory from settings if not provided
        if output_dir is None:
            settings = get_settings()
            output_dir = settings.DIAGRAMS_DIR

        # Ensure output directory exists
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            doc = fitz.open(self.current_file)
            page = doc[0]  # First page

            # Get list of images on the page
            image_list = page.get_images()

            if image_list:
                # Find the largest image (likely the diagram)
                largest_image = None
                max_size = 0

                for img_idx, img in enumerate(image_list):
                    xref = img[0]
                    base_image = doc.extract_image(xref)

                    # Calculate image size
                    size = base_image["width"] * base_image["height"]
                    if size > max_size:
                        max_size = size
                        largest_image = base_image

                if largest_image:
                    # Extract model name from PDF content
                    model_name = self._extract_model_name(self.current_file.name)
                    if model_name:
                        # Create output filename with just the model name
                        output_path = output_dir / f"{model_name}.png"

                        # Save image
                        with open(output_path, "wb") as f:
                            f.write(largest_image["image"])

                        return str(output_path)
        except Exception as e:
            print(f"Error extracting image: {e}")
        finally:
            if 'doc' in locals():
                doc.close()

        return None

    def process_pdf(self, filename: str) -> PDFData:
        """Process PDF file and extract structured data."""
        text = self._extract_text(filename)
        tables = self._extract_tables(text)

        # Initialize sections
        sections: Dict[str, SectionData] = {}

        # Extract features and advantages
        feat_adv_sections = self._parse_features_advantages(text, tables)
        if feat_adv_sections:
            sections.update(feat_adv_sections)

        # Process specification tables
        lines = text.split('\n')
        table_positions = []
        current_pos = 0

        # Find table positions
        for table in tables:
            if not table or not table[0]:  # Skip empty tables
                continue

            cells = [str(cell) for cell in table[0] if cell]
            first_row = ' '.join(cells)

            # Find position of this table in text
            while current_pos < len(lines):
                if first_row in lines[current_pos]:
                    table_positions.append(current_pos)
                    current_pos += 1
                    break
                current_pos += 1

        # Process tables with positions
        table_pairs = zip(tables, table_positions)
        for i, (table, pos) in enumerate(table_pairs):
            specs = self._parse_table_to_specs(table)
            if not specs:  # Skip if no specs found
                continue

            # Get section type
            section_name = self._determine_section_type(text, pos)
            if not section_name:
                continue

            # Format the section name
            section_key = self._format_section_name(section_name)
            if section_key:
                cat_specs = {
                    cat: CategorySpec(subcategories=subcat)
                    for cat, subcat in specs.items()
                }
                sections[section_key] = SectionData(categories=cat_specs)

        # Extract notes
        notes = self._extract_notes(text)
        notes_dict = {str(i + 1): note for i, note in enumerate(notes)} if notes else None

        # Extract diagram
        diagram_path = self._extract_model_diagram()

        return PDFData(
            sections=sections,
            notes=notes_dict,
            diagram_path=diagram_path
        )
