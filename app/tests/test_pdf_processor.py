import pytest
from unittest.mock import Mock, patch

from app.core.pdf_processor import PDFProcessor, PDFData
from app.models.pdf import (
    PDFTables, Table, TableRow, SpecDict
)


@pytest.fixture
def processor():
    """Create a PDFProcessor instance."""
    return PDFProcessor()


@pytest.fixture
def sample_pdf_text():
    """Sample PDF text with features, advantages, and specifications."""
    return """
Features and Advantages

• High Voltage Breakdown
  50kV

• Excellent Magnetic Properties
• Low Power Consumption
• Compact Design
• Reliable Performance

Electrical Specifications

Parameter    Value (Unit)
Voltage      24 (VDC)
Current      0.5 (A)
Power        12 (W)

Magnetic Specifications

Parameter    Value (Unit)
Pull Force   50 (N)
Gauss        1000 (G)

Physical/Operational Specifications

Parameter    Value (Unit)
Size         10x20x30 (mm)
Weight       100 (g)
Volume       6000 (cc)

(1) Note about voltage
(2) Note about current
"""


@pytest.fixture
def sample_tables():
    """Sample tables extracted from PDF."""
    return [
        [
            ["Parameter", "Value (Unit)"],
            ["Voltage", "24 (VDC)"],
            ["Current", "0.5 (A)"],
            ["Power", "12 (W)"]
        ],
        [
            ["Parameter", "Value (Unit)"],
            ["Pull Force", "50 (N)"],
            ["Gauss", "1000 (G)"]
        ],
        [
            ["Parameter", "Value (Unit)"],
            ["Size", "10x20x30 (mm)"],
            ["Weight", "100 (g)"],
            ["Volume", "6000 (cc)"]
        ]
    ]


def test_extract_text(processor, sample_pdf_text):
    """Test text extraction from PDF."""
    mock_pdf = Mock()
    mock_pdf.pages = [Mock(extract_text=Mock(return_value=sample_pdf_text))]
    
    with patch('pdfplumber.open', return_value=mock_pdf):
        text = processor._extract_text("test.pdf")
        assert text == sample_pdf_text
        assert processor.current_file == "test.pdf"


def test_extract_tables(processor, sample_tables):
    """Test table extraction from PDF."""
    mock_pdf = Mock()
    mock_pdf.pages = [Mock(extract_tables=Mock(return_value=sample_tables))]
    
    with patch('pdfplumber.open', return_value=mock_pdf):
        processor.current_file = "test.pdf"
        with patch('pathlib.Path.exists', return_value=True):
            tables = processor._extract_tables()
            
            assert isinstance(tables, PDFTables)
            assert len(tables.tables) == 3
            
            # Check first table structure
            first_table = tables.tables[0]
            assert isinstance(first_table, Table)
            assert len(first_table.rows) == 4
            
            # Check cell content
            first_row = first_table.rows[0]
            assert isinstance(first_row, TableRow)
            assert len(first_row.cells) == 2
            assert first_row.cells[0].value == "Parameter"
            assert first_row.cells[1].value == "Value (Unit)"


def test_parse_features_advantages(processor, sample_pdf_text):
    """Test parsing of features and advantages."""
    result = processor._parse_features_advantages(sample_pdf_text)
    
    assert "features" in result
    assert "advantages" in result
    
    # Check features
    features = result["features"][""]["subcategories"][""].value
    assert "High Voltage Breakdown" in features
    assert "Excellent Magnetic Properties" in features
    
    # Check advantages
    advantages = result["advantages"][""]["subcategories"][""].value
    assert "Low Power Consumption" in advantages
    assert "Compact Design" in advantages


def test_parse_table_to_specs(processor):
    """Test parsing table into specifications."""
    table = [
        ["Parameter", "Value (Unit)"],
        ["Voltage", "24 (VDC)"],
        ["Current", "0.5 (A)"]
    ]
    
    result = processor._parse_table_to_specs(table)
    
    assert "Parameter" in result
    voltage_spec = result["Parameter"]["Voltage"]
    assert voltage_spec.value == "24"
    assert voltage_spec.unit == "VDC"
    
    current_spec = result["Parameter"]["Current"]
    assert current_spec.value == "0.5"
    assert current_spec.unit == "A"


def test_determine_section_type(processor):
    """Test section type determination."""
    # Test electrical section
    electrical_specs = {
        "Parameter": {
            "Voltage": SpecDict(value="24", unit="VDC"),
            "Current": SpecDict(value="0.5", unit="A")
        }
    }
    assert processor._determine_section_type(electrical_specs) == "electrical"
    
    # Test magnetic section
    magnetic_specs = {
        "Parameter": {
            "Pull Force": SpecDict(value="50", unit="N"),
            "Gauss": SpecDict(value="1000", unit="G")
        }
    }
    assert processor._determine_section_type(magnetic_specs) == "magnetic"
    
    # Test physical section
    physical_specs = {
        "Parameter": {
            "Size": SpecDict(value="10x20x30", unit="mm"),
            "Weight": SpecDict(value="100", unit="g")
        }
    }
    assert processor._determine_section_type(physical_specs) == "physical"


def test_extract_diagram_path(processor):
    """Test diagram path extraction."""
    pdf_path = "uploads/pdfs/datasheet_M-123_rev1.pdf"
    diagram_path = processor._extract_diagram_path(pdf_path)
    assert diagram_path == "diagrams/123.png"


def test_process_pdf_integration(processor, sample_pdf_text, sample_tables):
    """Test complete PDF processing integration."""
    mock_pdf = Mock()
    mock_pdf.pages = [
        Mock(
            extract_text=Mock(return_value=sample_pdf_text),
            extract_tables=Mock(return_value=sample_tables)
        )
    ]
    
    with patch('pdfplumber.open', return_value=mock_pdf), \
         patch('pathlib.Path.exists', return_value=True):
        result = processor.process_pdf("test_M-123_rev1.pdf")
        
        assert isinstance(result, PDFData)
        assert "Electrical Specifications" in result.sections
        assert "Magnetic Specifications" in result.sections
        assert "Physical/Operational Specifications" in result.sections
        assert "features" in result.sections
        assert "advantages" in result.sections
        assert "notes" in result.sections
        assert result.diagram_path == "diagrams/123.png"


def test_process_pdf_validation(processor, sample_pdf_text):
    """Test PDF processing with invalid data."""
    mock_pdf = Mock()
    mock_pdf.pages = [
        Mock(
            extract_text=Mock(return_value=sample_pdf_text),
            # No tables = missing required sections
            extract_tables=Mock(return_value=[])
        )
    ]
    
    with patch('pdfplumber.open', return_value=mock_pdf), \
         patch('pathlib.Path.exists', return_value=True), \
         pytest.raises(ValueError) as exc_info:
        processor.process_pdf("test.pdf")
    
    assert "Missing required sections" in str(exc_info.value) 