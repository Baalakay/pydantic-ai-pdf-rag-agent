#!/usr/bin/env python3
import os
import sys
import json
from typing import Dict, List, Optional, Any, TypedDict
import pdfplumber


class SpecDict(TypedDict):
    unit: Optional[str]
    value: str


def parse_features_advantages(text: str) -> Dict[str, List[str]]:
    """Extract features and advantages using the same logic as pdf_reader.py."""
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


def try_parse_table(table: List[List[Any]]) -> Dict[str, Dict[str, SpecDict]]:
    """Try to parse a table based on its structure."""
    if not table or len(table) < 2:  # Need at least header + 1 row
        return {}
        
    # Get column structure
    columns = [str(col).strip() if col else "" for col in table[0]]
    
    # Skip features/advantages table
    if (len(columns) == 2 and 
            "Features" in columns[0] and 
            "Advantages" in columns[1]):
        return {}
        
    specs: Dict[str, Dict[str, SpecDict]] = {}
    current_category: Optional[str] = None
    
    # Process each row after header
    for row in table[1:]:
        try:
            # Clean row data
            row_data = [
                str(cell).strip() if cell else "" 
                for cell in row
            ]
            
            # Skip empty rows
            if not any(row_data):
                continue
                
            # Get main category and subcategory
            category = row_data[0] if row_data[0] else current_category
            subcategory = row_data[1] if row_data[1] else None
            
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
                    
                    # If we have a subcategory, nest under main category
                    if (subcategory and isinstance(subcategory, str) and 
                            category and isinstance(category, str)):
                        if subcategory not in specs[category]:
                            specs[category][subcategory] = {
                                "unit": unit,
                                "value": value
                            }
                    else:
                        # No subcategory, add directly to category
                        if category and isinstance(category, str):
                            specs[category] = {
                                "unit": unit,
                                "value": value
                            }
                
        except (ValueError, IndexError) as e:
            print(f"Error parsing row {row_data}: {str(e)}")
            continue
            
    return specs


def examine_pdf(filename: str) -> None:
    """Examine PDF structure and content."""
    print("\nRaw Text:")
    print("=" * 80)
    
    with pdfplumber.open(filename) as pdf:
        # Extract and print raw text
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        print(text)
        
        # Parse features and advantages from text
        features_advantages = parse_features_advantages(text)
        if features_advantages:
            print("\nParsed Features and Advantages:")
            print(json.dumps(features_advantages, indent=2))
        
        print("\nTable Analysis:")
        print("=" * 80)
        
        # Analyze each table
        for i, page in enumerate(pdf.pages):
            tables = page.extract_tables()
            
            for j, table in enumerate(tables):
                print(f"\nTable {j+1} Structure:\n")
                
                # Print column headers
                if table and table[0]:
                    print(f"Columns: {table[0]}\n")
                
                print("Row patterns:")
                # Analyze row patterns
                for row in table[1:] if table else []:
                    if not any(row):  # Skip empty rows
                        continue
                    row_data = [
                        str(cell).strip() if cell else "" 
                        for cell in row
                    ]
                    print(f"Row values: {row_data}")
                    
                    # Identify numeric columns
                    numeric_cols = []
                    for idx, cell in enumerate(row_data):
                        try:
                            is_numeric = (
                                cell and (
                                    cell.replace(".", "").replace("-", "")
                                        .replace("+", "").replace("E", "")
                                        .isdigit() or "to" in cell
                                )
                            )
                            if is_numeric:
                                numeric_cols.append(idx)
                        except Exception as e:
                            print(f"Error checking numeric: {str(e)}")
                            continue
                    if numeric_cols:
                        print(f"Numeric values in columns: {numeric_cols}")
                    print("-" * 40)
                
                # Try parsing specifications
                specs = try_parse_table(table)
                if specs:
                    print("\nParsed data:")
                    print(json.dumps(specs, indent=2))


def main() -> None:
    """Main function."""
    # Get list of PDFs
    pdf_dir = "uploads/pdfs"
    pdfs = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    if not pdfs:
        print("No PDFs found in uploads/pdfs directory")
        sys.exit(1)
        
    print("\nAvailable PDFs:")
    for i, pdf in enumerate(pdfs, 1):
        print(f"{i}. {pdf}")
        
    # Get user selection
    prompt = "\nSelect PDF number (or press Enter for first): "
    selection = input(prompt).strip()
    
    if not selection:
        selected_pdf = pdfs[0]
    else:
        try:
            idx = int(selection) - 1
            selected_pdf = pdfs[idx]
        except (ValueError, IndexError):
            print("Invalid selection")
            sys.exit(1)
            
    pdf_path = os.path.join(pdf_dir, selected_pdf)
    examine_pdf(pdf_path)


if __name__ == "__main__":
    main() 