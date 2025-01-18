from typing import Dict, List, Optional
import pdfplumber
from pathlib import Path
from app.models.pdf import PDFData, SectionData, CategorySpec, SpecValue


class PDFProcessor:
    def __init__(self) -> None:
        self.current_file: Optional[str] = None
        self.text_sections = ['features', 'advantages', 'notes']
        self.section_patterns = {
            'electrical': 'electrical specifications',
            'magnetic': 'magnetic specifications', 
            'physical': 'physical/operational specifications'
        }
        # Add section order for validation
        self.section_order = ['electrical', 'magnetic', 'physical']

    def _extract_text(self, filename: str) -> str:
        self.current_file = filename
        with pdfplumber.open(Path(filename)) as pdf:
            first_page = pdf.pages[0]
            return first_page.extract_text()

    def _parse_features_advantages(self, text: str) -> Dict[str, List[str]]:
        sections: Dict[str, List[str]] = {
            'features': [],
            'advantages': []
        }
        
        current_point = ""
        last_bullet_line = None
        bullet_points: List[str] = []
        collecting_features = False
        
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers
            if 'Features' in line or 'Advantages' in line:
                collecting_features = True
                continue
            elif any(header in line for header in [
                'Electrical Specifications',
                'Magnetic Specifications',
                'Physical/Operational Specifications'
            ]):
                collecting_features = False
                continue
                
            if not collecting_features:
                continue
                
            if '•' in line:
                if current_point:
                    bullet_points.append(current_point.strip())
                    current_point = ""
                    
                parts = line.split('•')
                for part in parts[1:]:
                    if part.strip():
                        if current_point:
                            bullet_points.append(current_point.strip())
                        current_point = part.strip()
                last_bullet_line = i
            elif line.strip():
                # Check if this line is a continuation
                if last_bullet_line is not None:
                    is_next_line = i == last_bullet_line + 1
                    is_short_word = len(line.split()) <= 2
                    if is_next_line and is_short_word:
                        # Handle Voltage Breakdown
                        if (bullet_points and 
                                "Voltage Breakdown" in bullet_points[-1]):
                            bullet_points[-1] += " " + line.strip()
                        elif (current_point and 
                                "Voltage Breakdown" in current_point):
                            current_point += " " + line.strip()
                    else:
                        if current_point:
                            bullet_points.append(current_point.strip())
                        current_point = line.strip()
        
        # Process collected bullet points
        if bullet_points:
            # Add the last point if exists
            if current_point:
                bullet_points.append(current_point.strip())
                
            # Clean up bullet points
            cleaned_points: List[str] = []
            seen = set()
            for point in bullet_points:
                if point not in seen and len(point.split()) > 1:
                    cleaned_points.append(point)
                    seen.add(point)
            bullet_points = cleaned_points
            
            # Classify points into features and advantages
            for i, point in enumerate(bullet_points, 1):
                if i <= 5 and i % 2 == 1:  # First three odd-numbered points
                    sections['features'].append(point)
                else:
                    sections['advantages'].append(point)
                    
        return sections

    def _extract_tables(self, text: str) -> List[List[List[str]]]:
        with pdfplumber.open(self.current_file) as pdf:
            first_page = pdf.pages[0]
            tables = first_page.extract_tables()
            return tables

    def _parse_table_to_specs(self, table: List[List[str]]) -> Dict[str, Dict[str, SpecValue]]:
        if not table:  # Empty table
            return {}
            
        # Clean first row
        first_row = [str(col).strip() if col else "" for col in table[0]]
        
        # Skip features/advantages table
        if len(first_row) == 2 and "Features" in first_row[0] and "Advantages" in first_row[1]:
            return {}
            
        specs: Dict[str, Dict[str, SpecValue]] = {}
        current_category: Optional[str] = None
        
        # Determine if first row is data by checking its structure
        # A data row will have a value in the first column and a unit/value in the last columns
        is_first_row_data = (
            len(first_row) >= 3 and  # Must have at least category, unit, value columns
            first_row[0] and  # Must have a category
            any(first_row[-2:])  # Must have either unit or value in last columns
        )
        
        # Process rows, including first row if it's data
        rows_to_process = table if is_first_row_data else table[1:]
        
        for row in rows_to_process:
            try:
                # Clean row data
                row_data = [str(cell).strip() if cell else "" for cell in row]
                
                # Skip completely empty rows
                if not any(row_data):
                    continue
                
                # Get category and subcategory
                category = row_data[0] if row_data[0] else current_category
                subcategory = row_data[1] if len(row_data) > 1 and row_data[1] else ""
                
                # Handle case where first column is empty but second isn't
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
                    
                    # Handle cases where unit and value might be in different positions
                    if len(row_data) > 3:
                        unit = row_data[2].strip() if row_data[2] else ""
                        value = row_data[3].strip() if row_data[3] else ""
                    else:
                        # If only 3 columns, assume last is value
                        unit = ""
                        value = row_data[2].strip() if row_data[2] else ""
                    
                    if value and category:
                        # If we have a non-empty subcategory, nest under main category
                        if subcategory:
                            specs[category][subcategory] = SpecValue(
                                unit=unit,
                                value=value
                            )
                        else:
                            # No subcategory or empty subcategory, add directly to category
                            specs[category][""] = SpecValue(
                                unit=unit,
                                value=value
                            )
                    
            except (ValueError, IndexError) as e:
                print(f"Error parsing row {row_data}: {str(e)}")
                continue
                
        return specs

    def _determine_section_type(self, text: str, table_start_index: int) -> str:
        """Find the section name that precedes this table position."""
        # Split text into lines and clean
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        
        # Find all section headers and their positions
        section_positions = []
        for i, line in enumerate(lines):
            if "Specifications" in line:
                # Keep the full section name
                section_positions.append((line.strip(), i))
        
        # Sort by position in document
        section_positions.sort(key=lambda x: x[1])
        
        # Find the section header that precedes our table
        section_name = section_positions[-1][0]  # Default to last section if can't determine
        for i in range(len(section_positions)):
            current_pos = section_positions[i][1]
            next_pos = section_positions[i + 1][1] if i + 1 < len(section_positions) else len(lines)
            
            if current_pos <= table_start_index < next_pos:
                section_name = section_positions[i][0]
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
                        notes.append(current_note.strip())
                        current_note = ""
                    parts = line.split('•')
                    for part in parts[1:]:
                        if part.strip():
                            notes.append(part.strip())
                else:
                    # Append to current note if it's a continuation
                    if current_note:
                        current_note += " " + line
                    else:
                        current_note = line
                        
        # Add the last note if there is one
        if current_note:
            notes.append(current_note.strip())
            
        return notes

    def _extract_model_name(self, text: str) -> str:
        """Extract the model name from the text."""
        lines = text.split('\n')
        for line in lines:
            if 'HSR-' in line:
                # Extract the part starting with HSR- and ending at the first space
                model_parts = line.split()
                for part in model_parts:
                    if 'HSR-' in part:
                        # Clean up any non-alphanumeric characters except -
                        model = ''.join(c for c in part if c.isalnum() or c == '-')
                        return model
        return ""

    def _format_section_name(self, name: str) -> str:
        """Format section name for JSON output by replacing non-alphanumeric chars with underscore."""
        # Replace any non-alphanumeric character with underscore and convert to title case
        formatted = ''.join('_' if not c.isalnum() else c for c in name)
        # Remove duplicate underscores if any
        while '__' in formatted:
            formatted = formatted.replace('__', '_')
        # Remove leading/trailing underscores and convert to title case
        return formatted.strip('_').title()

    def process_pdf(self, filename: str) -> PDFData:
        """Process a PDF file and return structured data."""
        # Extract text and tables
        text = self._extract_text(filename)
        tables = self._extract_tables(text)
        
        # Process tables into specifications first
        sections: Dict[str, SectionData] = {}
        
        # Get text lines for section header lookup
        lines = text.split('\n')
        table_positions = []
        current_pos = 0
        
        # Find positions of tables in the text
        for table in tables:
            if table and table[0]:  # Skip empty tables
                # Look for the table's first row in the text
                first_row = ' '.join(str(cell) for cell in table[0] if cell)
                while current_pos < len(lines):
                    if first_row in lines[current_pos]:
                        table_positions.append(current_pos)
                        current_pos += 1
                        break
                    current_pos += 1
        
        # Process tables with their positions
        for i, (table, pos) in enumerate(zip(tables, table_positions)):
            specs = self._parse_table_to_specs(table)
            if specs:  # Only process non-empty specs
                # Skip the features/advantages table
                if len(table[0]) == 2 and "Features" in str(table[0][0]) and "Advantages" in str(table[0][1]):
                    continue
                    
                section_name = self._determine_section_type(text, pos)
                formatted_name = self._format_section_name(section_name)
                sections[formatted_name] = SectionData(
                    categories={
                        cat: CategorySpec(subcategories={
                            "": {  # Using empty string as default subcategory
                                subcat: spec for subcat, spec in subcats.items()
                            }
                        })
                        for cat, subcats in specs.items()
                    }
                )
        
        # Parse features and advantages
        features_advantages = self._parse_features_advantages(text)
        
        # Extract notes
        notes = self._extract_notes(text)
        
        # Create and return document with sections first
        return PDFData(
            sections=sections,
            features_advantages={
                'features': features_advantages['features'],
                'advantages': features_advantages['advantages']
            } if features_advantages else None,
            notes={'notes': '\n'.join(notes)} if notes else None
        )
