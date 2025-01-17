import os
import re
import sys
from typing import Dict, List, Optional, Any
import pandas as pd

from app.core.pdf_processor import PDFProcessor
from app.models.comparison import compare_models

# Add the project root directory to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def find_pdf_by_model(
    model_keyword: str, 
    pdf_dir: str = "uploads/pdfs"
) -> Optional[str]:
    """Find a PDF file based on a model keyword."""
    # Strip any prefix/suffix and clean the model number
    model_match = re.search(r'\d+', model_keyword)
    if not model_match:
        return None
    
    model_base = model_match.group(0)
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            # Look for model number with optional hyphen and letters
            pattern = rf'{model_base}(?:-?[A-Za-z]{{0,5}})?'
            if re.search(pattern, filename):
                return os.path.join(pdf_dir, filename)
    return None


def process_models(model_list: List[str]) -> List[Dict[str, Any]]:
    """Process multiple PDFs and return their data."""
    model_data: List[Dict[str, Any]] = []
    processor = PDFProcessor()
    
    for model in model_list:
        pdf_path = find_pdf_by_model(model.strip())
        if not pdf_path:
            print(f"Could not find PDF for model {model}")
            continue
            
        try:
            result = processor.process_pdf(pdf_path)
            raw_data = result.model_dump()
            sections = raw_data.get("sections", [])
            
            # Transform data structure
            transformed_sections = {}
            
            # Handle sections based on type
            if isinstance(sections, list):
                for section in sections:
                    if not isinstance(section, dict):
                        continue
                        
                    section_type = section.get("section_type")
                    content = section.get("content")
                    
                    if not section_type or not content:
                        continue
                    
                    # Convert section_type to display name
                    if section_type == "features_advantages":
                        section_name = "Features and Advantages"
                    else:
                        # Convert snake_case to Title Case
                        words = section_type.split("_")
                        if section_type == "physical":
                            section_name = (
                                "Physical/Operational Specifications"
                            )
                        else:
                            # Add "Specifications" suffix
                            title_words = [word.title() for word in words]
                            section_name = (
                                " ".join(title_words) + " Specifications"
                            )
                    
                    transformed_sections[section_name] = content
            else:
                continue
            
            # Add diagram path to Physical/Operational Specifications
            phys_specs_key = "Physical/Operational Specifications"
            if phys_specs_key in transformed_sections:
                phys_specs = transformed_sections[phys_specs_key]
                if isinstance(phys_specs, dict):
                    # Remove any existing diagram entries
                    if "Diagram" in phys_specs:
                        del phys_specs["Diagram"]
                        
                    # Add new diagram entry
                    diagram_path = raw_data.get("diagram_path")
                    if diagram_path:  # Only add if path exists
                        phys_specs["Diagram"] = {
                            "": {
                                "unit": "",
                                "value": diagram_path
                            }
                        }
            
            data = {
                "model": model.strip().upper(),
                "sections": transformed_sections,
                "diagram_path": raw_data.get("diagram_path", "")
            }
            
            model_data.append(data)
            
        except Exception as e:
            print(f"Error processing {model}: {str(e)}")
            continue
    
    return model_data


def display_dataframe(df: pd.DataFrame, title: str) -> None:
    """Display a dataframe with a title."""
    if not df.empty:
        print("\n" + "=" * 80)
        print(title + ":")
        print("=" * 80)
        
        # Clean up the data
        if 'Finding' in df.columns:
            df['Finding'] = df['Finding'].str.strip()
            df['Finding'] = df['Finding'].apply(lambda x: ' '.join(x.split()))
            # For Key Findings, just print the findings without the header
            for _, row in df.iterrows():
                print(row['Finding'])
        else:
            # Format with minimal spacing for other tables
            with pd.option_context(
                'display.max_rows', None,
                'display.max_columns', None,
                'display.width', None,
                'display.max_colwidth', None,
                'display.show_dimensions', False,
                'display.expand_frame_repr', False,
                'display.unicode.east_asian_width', False,
                'display.colheader_justify', 'left'
            ):
                # Calculate minimum column widths based on content
                col_widths = {}
                for col in df.columns:
                    col_content = df[col].astype(str)
                    max_length = max(col_content.str.len().max(), len(str(col)))
                    col_widths[col] = max_length + 1  # Add 1 for minimal spacing
                
                # Create format string for each row
                format_str = ' '.join('{:<' + str(width) + '}' 
                                    for width in col_widths.values())
                
                # Print headers
                headers = [str(col) for col in df.columns]
                print(format_str.format(*headers))
                
                # Print rows
                for _, row in df.iterrows():
                    print(format_str.format(*[str(val) for val in row.values]))


def main() -> None:
    """Main function."""
    if len(sys.argv) < 2:
        print("Please provide model numbers as arguments")
        print("Example: python test_comparison.py '520R, 630'")
        sys.exit(1)

    # Get model numbers from command line
    model_numbers = [m.strip() for m in sys.argv[1].split(",")]
    if len(model_numbers) < 2:
        print("At least two models are needed for comparison")
        sys.exit(1)

    try:
        # Process models
        model_data = process_models(model_numbers)
        if len(model_data) < 2:
            print("At least two models are needed for comparison")
            sys.exit(1)

        # Compare models and display results
        result = compare_models(model_data)
        display_dataframe(
            result.electrical_specs_df, 
            "Electrical Specifications"
        )
        display_dataframe(
            result.magnetic_specs_df, 
            "Magnetic Specifications"
        )
        display_dataframe(
            result.physical_specs_df,
            "Physical/Operational Specifications"
        )
        display_dataframe(
            result.spec_differences_df, 
            "Specification Differences"
        )
        display_dataframe(
            result.key_findings_df, 
            "Key Findings"
        )

    except Exception as e:
        print(f"Error during comparison: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 