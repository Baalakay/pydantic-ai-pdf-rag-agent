from typing import Dict, List, Optional, Union, Any, cast

from app.models.pdf import SpecDict


class PDFSectionParser:
    """Parser for PDF sections."""

    def parse_section(
        self, section: str, content: Union[List[str], List[List[Any]]]
    ) -> Union[List[str], Dict[str, Dict[str, SpecDict]], None]:
        """Parse a section based on its type."""
        if section in ["features", "advantages"]:
            return self._parse_bullet_points(content)
        elif section in ["electrical", "magnetic", "physical"]:
            return self._parse_table_specs(cast(List[List[Any]], content))
        return None

    def _parse_bullet_points(
        self, content: Union[List[str], List[List[Any]]]
    ) -> List[str]:
        """Parse bullet points from text or table content."""
        points: List[str] = []
        
        if isinstance(content, list) and content:
            if isinstance(content[0], str):
                # Handle text content
                for line in cast(List[str], content):
                    if "•" in line:
                        # Handle bulleted content
                        for point in line.split("•"):
                            if point.strip():
                                points.append(point.strip())
                    else:
                        # Handle non-bulleted content
                        if line.strip():
                            points.append(line.strip())
            else:
                # Handle table content
                for row in cast(List[List[Any]], content):
                    if row and row[0]:
                        points.append(str(row[0]).strip())
        
        # Clean up points
        cleaned_points: List[str] = []
        seen = set()
        for point in points:
            if point not in seen and len(point.split()) > 1:
                cleaned_points.append(point)
                seen.add(point)
                    
        return cleaned_points

    def _parse_table_specs(
        self,
        table: List[List[Any]]
    ) -> Dict[str, Dict[str, SpecDict]]:
        """Parse specifications from a table structure."""
        if not table or len(table) < 2:  # Need at least header and one row
            return {}
            
        specs: Dict[str, Dict[str, SpecDict]] = {}
        current_category: Optional[str] = None
        
        # Process each row after header
        for row in table[1:]:
            try:
                # Clean row data
                row_data = [str(cell).strip() if cell else "" for cell in row]
                
                # Skip empty rows
                if not any(row_data):
                    continue
                    
                # Get main category and subcategory
                category = row_data[0] if row_data[0] else current_category
                subcategory = (
                    row_data[1] if len(row_data) > 1 and row_data[1] else None
                )
                
                if category and isinstance(category, str):
                    current_category = category
                    if category not in specs:
                        specs[category] = {}
                        
                # Get unit and value
                if len(row_data) > 2:
                    unit = None
                    if row_data[2]:
                        unit = row_data[2].strip()
                    
                    if len(row_data) > 3 and row_data[3]:
                        value = row_data[3].strip()
                        spec = SpecDict(unit=unit, value=value)
                        
                        # If we have a subcategory, nest under main category
                        if (subcategory and isinstance(subcategory, str) and 
                                category and isinstance(category, str)):
                            if subcategory not in specs[category]:
                                specs[category][subcategory] = spec
                        else:
                            # No subcategory, add directly to category
                            if category and isinstance(category, str):
                                specs[category] = {"": spec}
                    
            except (ValueError, IndexError) as e:
                print(f"Error parsing row {row_data}: {str(e)}")
                continue
                    
        return specs 