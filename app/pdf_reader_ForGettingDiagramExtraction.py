import pdfplumber
from typing import List, Optional, Tuple, Dict
import os
import re
import fitz  # type: ignore  # PyMuPDF
from app.models.comparison import ModelSpecs, ComparisonResult, ElectricalSpecs, MagneticSpecs, PhysicalSpecs, KeyDifferences

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
        'advantages': [],
        'electrical': [],
        'magnetic': [],
        'physical': [],
        'notes': []
    }

    current_section = None
    current_point = ""
    in_notes = False
    last_bullet_line = None
    collecting_features = False
    bullet_points = []

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]
        text = page.extract_text()
        lines = text.split('\n')

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Detect section headers
            if 'Features' in line or 'Advantages' in line:
                collecting_features = True
                current_section = None  # Reset other sections
                in_notes = False
                continue
            elif 'Electrical Specifications' in line:
                collecting_features = False
                current_section = 'electrical'
                in_notes = False
                continue
            elif 'Magnetic Specifications' in line:
                collecting_features = False
                current_section = 'magnetic'
                in_notes = False
                continue
            elif 'Physical/Operational Specifications' in line:
                collecting_features = False
                current_section = 'physical'
                in_notes = False
                continue

            # Handle Features and Advantages collection
            if collecting_features:
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
                            # Special handling for Voltage Breakdown continuation
                            if bullet_points and "Voltage Breakdown" in bullet_points[-1]:
                                bullet_points[-1] += " " + line.strip()
                            elif current_point and "Voltage Breakdown" in current_point:
                                current_point += " " + line.strip()
                        else:
                            if current_point:
                                bullet_points.append(current_point.strip())
                            current_point = line.strip()
                continue

            # Handle notes section
            if re.match(r'\(\d+\)', line):
                current_section = 'notes'
                in_notes = True
                sections['notes'].append(line)
                continue

            if in_notes and line:
                if not re.match(r'\(\d+\)', line):
                    if sections['notes']:
                        sections['notes'][-1] = sections['notes'][-1] + ' ' + line
                    else:
                        sections['notes'].append(line)
                else:
                    sections['notes'].append(line)
                continue

            # Handle other sections
            if current_section and not in_notes:
                if '•' in line:
                    if current_point:
                        sections[current_section].append(current_point.strip())
                        current_point = ""
                    parts = line.split('•')
                    for part in parts[1:]:
                        if part.strip():
                            sections[current_section].append(part.strip())
                else:
                    if line.strip() and len(line.split()) > 1:
                        sections[current_section].append(line.strip())

    # Process collected bullet points for features and advantages
    if bullet_points:
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
        for i, point in enumerate(bullet_points, 1):
            if i <= 5 and i % 2 == 1:  # First three odd-numbered points
                sections['features'].append(point)
            else:
                sections['advantages'].append(point)

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
    query_type: 'section' or 'attribute' or 'diagram'
    target: section name or attribute name
    """
    query = query.lower()

    # Check for diagram queries first
    if any(word in query for word in ['diagram', 'drawing', 'schematic', 'dimension', 'picture', 'image']):
        return 'diagram', None

    # Section patterns
    section_patterns = {
        'electrical': r'electrical|electrical spec',
        'magnetic': r'magnetic|magnetic spec',
        'physical': r'physical|operational|physical spec|operational spec',
        'features': r'features?|advantages?',
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

    return 'section', None

def search_pdf(query: str) -> Tuple[Optional[str], List[str]]:
    """
    Search PDFs based on a natural language query.
    Returns tuple of (model_number, relevant_text_sections).
    For diagram queries, returns tuple of (model_number, [diagram_path]).
    """
    model = extract_model_from_query(query)
    if not model:
        return None, []

    pdf_path = find_pdf_by_model(model)
    if not pdf_path:
        return model, []

    query_type, target = identify_query_type(query)

    # Handle diagram queries
    if query_type == 'diagram':
        diagram_path = extract_model_diagram(pdf_path)
        if diagram_path:
            return model, [f"Diagram saved to: {diagram_path}"]
        return model, ["No diagram found"]

    # Handle text-based queries
    sections = extract_sections(pdf_path)
    results = []

    # Extract diagram for all queries
    diagram_path = extract_model_diagram(pdf_path)
    if diagram_path:
        results.extend(['\nDiagram:', f"Diagram saved to: {diagram_path}"])

    if query_type == 'section' and target:
        if target == 'features':
            # For features/advantages queries, return both
            results.extend(['Features:'])
            results.extend(sections['features'])
            results.extend(['\nAdvantages:'])
            results.extend(sections['advantages'])
        else:
            # Return other sections as normal
            results.extend(sections.get(target, []))
    elif query_type == 'attribute' and target:
        # Search for specific attribute across all sections
        for section_items in sections.values():
            for item in section_items:
                if target in item.lower():
                    results.append(item)
    else:
        # For general queries, return all sections with headers
        results.extend(['Features:'])
        results.extend(sections['features'])
        results.extend(['\nAdvantages:'])
        results.extend(sections['advantages'])
        results.extend(['\nElectrical Specifications:'])
        results.extend(sections['electrical'])
        results.extend(['\nMagnetic Specifications:'])
        results.extend(sections['magnetic'])
        results.extend(['\nPhysical/Operational Specifications:'])
        results.extend(sections['physical'])
        results.extend(['\nNotes:'])
        results.extend(sections['notes'])

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

def extract_model_diagram(pdf_path: str, output_dir: str = "uploads/images") -> Optional[str]:
    """Extract the model diagram image from the PDF.
    Returns the path to the saved image if successful, None otherwise."""
    os.makedirs(output_dir, exist_ok=True)

    try:
        doc = fitz.open(pdf_path)
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
                # Create output filename
                pdf_name = os.path.basename(pdf_path)
                img_name = pdf_name.replace('.pdf', '_diagram.png')
                output_path = os.path.join(output_dir, img_name)

                # Save image
                with open(output_path, "wb") as f:
                    f.write(largest_image["image"])

                return output_path
    except Exception as e:
        print(f"Error extracting image: {e}")
    finally:
        if 'doc' in locals():
            doc.close()

    return None

def extract_model_specs(pdf_path: str) -> ModelSpecs:
    """Extract all specifications for a model and return as structured data."""
    sections = extract_sections(pdf_path)

    # Extract model number from pdf path
    match = re.search(r'HSR-(\d+[RFW]?)-?Series', os.path.basename(pdf_path), re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not extract model number from PDF path: {pdf_path}")
    model = match.group(1)

    # Get diagram path
    diagram_path = extract_model_diagram(pdf_path)

    # Parse electrical specifications
    electrical = ElectricalSpecs(
        power_watts=None,
        voltage_switching=None,
        voltage_breakdown=None,
        current_switching=None,
        current_carry=None,
        resistance_contact=None,
        resistance_insulation=None,
        capacitance=None,
        temperature_operating=None,
        temperature_storage=None
    )
    for spec in sections['electrical']:
        if 'Power Watts' in spec:
            electrical.power_watts = spec
        elif 'Voltage Switching' in spec:
            electrical.voltage_switching = spec
        elif 'Breakdown VDC' in spec:
            electrical.voltage_breakdown = spec
        elif 'Current Switching' in spec:
            electrical.current_switching = spec
        elif 'Carry Amp' in spec:
            electrical.current_carry = spec
        elif 'Contact Resistance' in spec:
            electrical.resistance_contact = spec
        elif 'Insulation Resistance' in spec:
            electrical.resistance_insulation = spec
        elif 'Capacitance' in spec:
            electrical.capacitance = spec
        elif 'Operating °C' in spec:
            electrical.temperature_operating = spec
        elif 'Storage °C' in spec:
            electrical.temperature_storage = spec

    # Parse magnetic specifications
    magnetic = MagneticSpecs(
        pull_in_range=None,
        test_coil=None
    )
    for spec in sections['magnetic']:
        if 'Pull - In Range' in spec:
            magnetic.pull_in_range = spec
        elif 'Test Coil' in spec:
            magnetic.test_coil = spec

    # Parse physical specifications
    physical = PhysicalSpecs(
        volume=None,
        contact_material=None,
        operate_time=None,
        release_time=None
    )
    for spec in sections['physical']:
        if 'Volume' in spec:
            physical.volume = spec
        elif 'Contact Material' in spec:
            physical.contact_material = spec
        elif 'Operate Time' in spec:
            physical.operate_time = spec
        elif 'Release Time' in spec:
            physical.release_time = spec

    return ModelSpecs(
        model=model,
        features=sections['features'],
        advantages=sections['advantages'],
        electrical=electrical,
        magnetic=magnetic,
        physical=physical,
        notes=sections['notes'],
        diagram_path=diagram_path
    )

def extract_models_from_query(query: str) -> List[str]:
    """Extract multiple model numbers from a comparison query."""
    return re.findall(r'(\d+[RFWrfw]?)', query)

def compare_models(query: str) -> Optional[ComparisonResult]:
    """Compare specifications of multiple models (up to 3)."""
    models = extract_models_from_query(query)
    if not models or len(models) > 3:
        return None

    query = query.lower()
    # Determine comparison type
    if 'electrical' in query:
        comparison_type = 'electrical'
    elif 'magnetic' in query:
        comparison_type = 'magnetic'
    elif 'physical' in query or 'operational' in query:
        comparison_type = 'physical'
    elif 'features' in query or 'advantages' in query:
        comparison_type = 'features'
    else:
        comparison_type = 'full'

    # Get specs for each model
    model_specs = []
    for model in models:
        pdf_path = find_pdf_by_model(model)
        if pdf_path:
            specs = extract_model_specs(pdf_path)
            model_specs.append(specs)

    if not model_specs or len(model_specs) < 2:
        return None

    # Calculate key differences
    key_differences = KeyDifferences(
        power=None,
        voltage=None,
        current=None,
        size=None,
        temperature=None,
        other=[]
    )

    # Compare first two models for differences
    model1, model2 = model_specs[0], model_specs[1]

    # Power difference
    if model1.electrical.power_watts and model2.electrical.power_watts:
        match1 = re.search(r'(\d+(?:\.\d+)?)', model1.electrical.power_watts)
        match2 = re.search(r'(\d+(?:\.\d+)?)', model2.electrical.power_watts)
        if match1 and match2:
            power1 = float(match1.group(1))
            power2 = float(match2.group(1))
            ratio = power2 / power1
            key_differences.power = f"{model2.model} handles {ratio:.1f}x more power ({power2}W vs {power1}W)"

    # Voltage difference
    if model1.electrical.voltage_switching and model2.electrical.voltage_switching:
        match1 = re.search(r'(\d+(?:\.\d+)?)', model1.electrical.voltage_switching)
        match2 = re.search(r'(\d+(?:\.\d+)?)', model2.electrical.voltage_switching)
        if match1 and match2:
            v1 = float(match1.group(1))
            v2 = float(match2.group(1))
            key_differences.voltage = f"{model2.model} has higher voltage ratings ({v2}V vs {v1}V switching)"

    # Current difference
    if model1.electrical.current_switching and model2.electrical.current_switching:
        match1 = re.search(r'(\d+(?:\.\d+)?)', model1.electrical.current_switching)
        match2 = re.search(r'(\d+(?:\.\d+)?)', model2.electrical.current_switching)
        if match1 and match2:
            i1 = float(match1.group(1))
            i2 = float(match2.group(1))
            key_differences.current = f"{model2.model} can switch higher currents ({i2}A vs {i1}A)"

    # Size difference
    if model1.physical.volume and model2.physical.volume:
        match1 = re.search(r'(\d+(?:\.\d+)?)', model1.physical.volume)
        match2 = re.search(r'(\d+(?:\.\d+)?)', model2.physical.volume)
        if match1 and match2:
            vol1 = float(match1.group(1))
            vol2 = float(match2.group(1))
            ratio = vol2 / vol1
            key_differences.size = f"{model2.model} is larger with ~{ratio:.1f}x the capsule volume"

    # Temperature range
    if model1.electrical.temperature_operating and model2.electrical.temperature_operating:
        match1 = re.search(r'-(\d+)', model1.electrical.temperature_operating)
        match2 = re.search(r'-(\d+)', model2.electrical.temperature_operating)
        if match1 and match2:
            temp1 = match1.group(1)
            temp2 = match2.group(1)
            if temp1 != temp2:
                key_differences.temperature = f"{model2.model} has wider temperature range (-{temp2}°C vs -{temp1}°C minimum)"

    # Add other notable differences
    if model1.features and model2.features:
        unique_features = set(model2.features) - set(model1.features)
        if unique_features:
            key_differences.other.extend([f"Unique {model2.model} feature: {f}" for f in unique_features])

    return ComparisonResult(
        models=model_specs,
        comparison_type=comparison_type,
        key_differences=key_differences
    )

if __name__ == "__main__":
    test_pdf()