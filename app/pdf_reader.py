import pdfplumber
from typing import List, Optional, Tuple, Dict
import os
import re

def find_pdf_by_model(model_keyword: str, pdf_dir: str = "uploads/pdfs") -> Optional[str]:
    """Find a PDF file based on a model keyword."""
    clean_keyword = model_keyword.upper().replace('HSR-', '').replace('HSR', '')
    
    for filename in os.listdir(pdf_dir):
        if filename.endswith('.pdf'):
            match = re.search(r'HSR-(\d+[RFW]?)-?Series', filename, re.IGNORECASE)
            if match:
                model_number = match.group(1)
                if clean_keyword in model_number or model_number in clean_keyword:
                    return os.path.join(pdf_dir, filename)
    return None

def extract_sections(pdf_path: str) -> Dict[str, List[str]]:
    """Extract and categorize sections from the PDF."""
    sections: Dict[str, List[str]] = {
        'features': [],
        'electrical': [],
        'magnetic': [],
        'physical': [],
        'notes': []
    }
    
    current_section = None
    current_point = ""
    
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        lines = text.split('\n')
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Detect section headers
            if 'Electrical Specifications' in line:
                current_section = 'electrical'
                continue
            elif 'Magnetic Specifications' in line:
                current_section = 'magnetic'
                continue
            elif 'Physical/Operational Specifications' in line:
                current_section = 'physical'
                continue
            elif line.startswith('('):  # Notes section
                current_section = 'notes'
            elif not current_section and ('Features' in line or 'Advantages' in line):
                current_section = 'features'
                continue
                
            if current_section:
                if '•' in line:
                    if current_point:
                        sections[current_section].append(current_point.strip())
                        current_point = ""
                    parts = line.split('•')
                    for part in parts[1:]:
                        if part.strip():
                            sections[current_section].append(part.strip())
                else:
                    # Handle regular lines (like specifications)
                    if line.strip() and len(line.split()) > 1:  # Avoid single words
                        sections[current_section].append(line.strip())

    return sections

def extract_model_from_query(query: str) -> Optional[str]:
    """Extract model number from a natural language query."""
    model_match = re.search(r'(\d+[RFWrfw]?)', query)
    if model_match:
        return model_match.group(1)
    return None

def identify_query_type(query: str) -> Tuple[str, Optional[str]]:
    """
    Identify if the query is for a section or specific attribute.
    Returns tuple of (query_type, target)
    query_type: 'section' or 'attribute'
    target: section name or attribute name
    """
    query = query.lower()
    
    # Section patterns
    section_patterns = {
        'electrical': r'electrical|electrical spec',
        'magnetic': r'magnetic|magnetic spec',
        'physical': r'physical|operational|physical spec|operational spec',
        'features': r'features|advantages',
        'notes': r'notes|footnotes'
    }
    
    # Check for section queries
    for section, pattern in section_patterns.items():
        if re.search(pattern, query):
            return 'section', section
            
    # Check for specific attributes
    attribute_patterns = [
        r'release time', r'operate time', r'temperature', r'current',
        r'voltage', r'power', r'resistance', r'capacitance',
        r'ampere turns', r'test coil', r'volume', r'contact material'
    ]
    
    for pattern in attribute_patterns:
        if re.search(pattern, query):
            return 'attribute', pattern
            
    return 'section', None  # Default to full section if can't identify

def search_pdf(query: str) -> Tuple[Optional[str], List[str]]:
    """
    Search PDFs based on a natural language query.
    Returns tuple of (model_number, relevant_text_sections).
    """
    model = extract_model_from_query(query)
    if not model:
        return None, []
    
    pdf_path = find_pdf_by_model(model)
    if not pdf_path:
        return model, []
    
    sections = extract_sections(pdf_path)
    query_type, target = identify_query_type(query)
    
    results = []
    if query_type == 'section' and target:
        # Return entire section
        results.extend(sections.get(target, []))
    elif query_type == 'attribute' and target:
        # Search for specific attribute across all sections
        for section_items in sections.values():
            for item in section_items:
                if target in item.lower():
                    results.append(item)
    
    return model, results

def test_pdf() -> None:
    # Test queries
    queries = [
        "What is the release time of the 1016r",
        "Show me all the Electrical specs for 1016r",
        "What is the operating temperature of 520R"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        model, results = search_pdf(query)
        
        if model:
            print(f"Results for model {model}:")
            if results:
                for result in results:
                    print(f"- {result}")
            else:
                print("No relevant information found")
        else:
            print("No model number found in query")

if __name__ == "__main__":
    test_pdf()
