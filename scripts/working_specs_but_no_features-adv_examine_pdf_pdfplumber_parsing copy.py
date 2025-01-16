#!/usr/bin/env python3
import os
import sys
import json
from typing import Dict, List, Any, Optional, TypedDict
import pdfplumber


class SpecDict(TypedDict):
    unit: Optional[str]
    value: str


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
        
    specs = {}
    current_category = None
    
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
            
            if category:
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
                    if subcategory:
                        if subcategory not in specs[category]:
                            specs[category][subcategory] = {
                                "unit": unit,
                                "value": value
                            }
                    else:
                        # No subcategory, add directly to category
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
                
                # Try parsing the table
                specs = try_parse_table(table)
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