from typing import Dict, List, Optional, Any
import pdfplumber
import json
from app.models.pdf import PDFDocument, PDFSection, SpecDict


class PDFProcessor:
    def __init__(self):
        self.current_file = None
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
        with pdfplumber.open(filename) as pdf:
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

    def _parse_table_to_specs(self, table: List[List[str]]) -> Dict[str, Dict[str, SpecDict]]:
        if not table:  # Empty table
            return {}
            
        # Clean first row
        first_row = [str(col).strip() if col else "" for col in table[0]]
        
        # Skip features/advantages table
        if len(first_row) == 2 and "Features" in first_row[0] and "Advantages" in first_row[1]:
            return {}
            
        specs: Dict[str, Dict[str, SpecDict]] = {}
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
                        unit = row_data[2].strip() if row_data[2] else None
                        value = row_data[3].strip() if row_data[3] else None
                    else:
                        # If only 3 columns, assume last is value
                        value = row_data[2].strip() if row_data[2] else None
                    
                    if value and category:
                        # If we have a non-empty subcategory, nest under main category
                        if subcategory:
                            specs[category][subcategory] = SpecDict(
                                unit=unit,
                                value=value
                            )
                        else:
                            # No subcategory or empty subcategory, add directly to category
                            specs[category][""] = SpecDict(
                                unit=unit,
                                value=value
                            )
                    
            except (ValueError, IndexError) as e:
                print(f"Error parsing row {row_data}: {str(e)}")
                continue
                
        return specs

    def _determine_section_type(self, specs: Dict[str, Dict[str, SpecDict]]) -> str:
        """Determine section type based on the content and structure of the specifications."""
        # Get all units and values to analyze the type of measurements
        units = []
        values = []
        for category in specs.values():
            for spec in category.values():
                if spec.unit:
                    units.append(spec.unit.lower())
                if spec.value:
                    values.append(spec.value.lower())

        # Analyze measurement patterns
        electrical_patterns = any(
            unit.endswith(suffix) for unit in units
            for suffix in ['vdc', 'amp', 'ohm', 'pf', '°c']
        )
        
        magnetic_patterns = any(
            'ampere turns' in unit.lower() or
            'gauss' in unit.lower() or
            'test coil' in ' '.join(values).lower()
            for unit in units
        )
        
        physical_patterns = any(
            unit.endswith(suffix) for unit in units
            for suffix in ['mseconds', 'cc', 'mm']
        ) or any(
            'material' in key.lower() or
            'time' in key.lower() or
            'volume' in key.lower()
            for key in specs.keys()
        )

        # Determine section based on strongest pattern match
        if electrical_patterns and not magnetic_patterns and not physical_patterns:
            return 'electrical'
        elif magnetic_patterns and not physical_patterns:
            return 'magnetic'
        elif physical_patterns:
            return 'physical'
        
        # If no clear pattern, analyze the measurement context
        measurements = ' '.join(list(specs.keys()) + units + values).lower()
        if any(term in measurements for term in ['voltage', 'current', 'resistance', 'capacitance', 'temperature']):
            return 'electrical'
        elif any(term in measurements for term in ['pull', 'coil', 'magnetic', 'gauss']):
            return 'magnetic'
        elif any(term in measurements for term in ['material', 'time', 'volume', 'dimension']):
            return 'physical'
            
        # Default based on most common pattern in this type of document
        return 'electrical'

    def _extract_sections(self, text: str) -> List[PDFSection]:
        sections = []
        
        # Process features and advantages
        features_advantages = self._parse_features_advantages(text)
        if features_advantages['features'] or features_advantages['advantages']:
            print("\nFeatures and Advantages:")
            print(json.dumps(features_advantages, indent=2))
            print()
            sections.append(PDFSection(
                section_type='features_advantages',
                content=features_advantages
            ))
            
        # Process tables for specifications
        tables = self._extract_tables(text)
        
        # Process each table
        for table in tables:
            specs = self._parse_table_to_specs(table)
            if specs:
                # Determine section type based on content
                section_type = self._determine_section_type(specs)
                
                # Convert SpecDict objects to dictionaries
                json_data = {}
                for category, subcategories in specs.items():
                    json_data[category] = {}
                    for subcategory, spec in subcategories.items():
                        json_data[category][subcategory] = {
                            "unit": spec.unit if spec.unit is not None else "",
                            "value": spec.value if spec.value is not None else ""
                        }
                
                # Print section-specific header
                section_header = {
                    'electrical': 'Electrical',
                    'magnetic': 'Magnetic',
                    'physical': 'Physical/Operational'
                }
                print(f"\n{section_header[section_type]} Specifications:")
                print(json.dumps(json_data, indent=2))
                print()
                sections.append(PDFSection(
                    section_type=section_type,
                    content=specs
                ))
                    
        # Process notes section
        notes_content = []
        in_notes = False
        for line in text.split('\n'):
            if 'Notes:' in line:
                in_notes = True
            elif in_notes and line.strip():
                notes_content.append(line.strip())
                
        if notes_content:
            sections.append(PDFSection(
                section_type='notes',
                content='\n'.join(notes_content)
            ))
            
        return sections

    def process_pdf(self, filename: str) -> PDFDocument:
        text = self._extract_text(filename)
        sections = self._extract_sections(text)
        return PDFDocument(
            filename=filename,
            sections=sections,
            metadata={},
            diagram_path=None,
            page_count=1
        )
