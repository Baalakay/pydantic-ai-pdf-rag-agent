# PDF RAG Agent Project Notes

## Current Libraries
- FastAPI - Web framework
- Pydantic/Pydantic-AI - Data validation and settings management
- PDFPlumber - PDF text extraction
- PyMuPDF (fitz) - PDF diagram extraction
- OpenAI - Embeddings and chat completions
- Logfire - Structured logging
- Tiktoken - Token counting
- Python-multipart - File upload handling

## Implementation Plan

### 1. Model Organization
- Consolidate all Pydantic models in `app/models/`
- Follow Pydantic v2 best practices with field validation
- Models structure:
  ```
  app/models/
  ├── __init__.py      # Exports all models
  ├── pdf.py           # PDF document models
  ├── comparison.py    # Comparison models
  ├── chat.py          # Chat/message models
  └── vector.py        # Vector store models
  ```

#### Key Models:
```python
# pdf.py
class PDFSection(BaseModel):
    section_type: str  # features, advantages, electrical, magnetic, physical
    content: str
    bullet_points: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PDFDocument(BaseModel):
    filename: str
    sections: List[PDFSection]
    metadata: Dict[str, Any] = Field(default_factory=dict)
    diagram_path: Optional[str] = None

# comparison.py
class ElectricalSpecs(BaseModel):
    power_watts: Optional[str] = None
    voltage_switching: Optional[str] = None
    voltage_breakdown: Optional[str] = None
    current_switching: Optional[str] = None
    current_carry: Optional[str] = None
    resistance_contact: Optional[str] = None
    resistance_insulation: Optional[str] = None
    capacitance: Optional[str] = None
    temperature_operating: Optional[str] = None
    temperature_storage: Optional[str] = None

class MagneticSpecs(BaseModel):
    pull_in_range: Optional[str] = None
    test_coil: Optional[str] = None

class PhysicalSpecs(BaseModel):
    volume: Optional[str] = None
    contact_material: Optional[str] = None
    operate_time: Optional[str] = None
    release_time: Optional[str] = None

class ModelSpecs(BaseModel):
    model: str
    features: List[str] = Field(default_factory=list)
    advantages: List[str] = Field(default_factory=list)
    electrical: ElectricalSpecs = Field(default_factory=ElectricalSpecs)
    magnetic: MagneticSpecs = Field(default_factory=MagneticSpecs)
    physical: PhysicalSpecs = Field(default_factory=PhysicalSpecs)
    notes: List[str] = Field(default_factory=list)
    diagram_path: Optional[str] = None

class KeyDifferences(BaseModel):
    power: Optional[str] = None
    voltage: Optional[str] = None
    current: Optional[str] = None
    size: Optional[str] = None
    temperature: Optional[str] = None
    other: List[str] = Field(default_factory=list)

class ComparisonResult(BaseModel):
    models: List[ModelSpecs]
    comparison_type: str  # full, electrical, magnetic, physical, or features
    key_differences: Optional[KeyDifferences] = None
```

### 2. PDF Processing Enhancement
1. Port section extraction from `pdf_reader.py` to `PDFProcessor`
2. Maintain special handling for Features/Advantages sections
3. Add bullet point collection
4. Keep diagram extraction using PyMuPDF
5. Store extracted data using new Pydantic models

### 3. Vector Store Integration
1. Create vector entries for each section
2. Store metadata:
   - Section type (electrical, magnetic, etc.)
   - Parent document info
   - Bullet point indicators
3. Optimize search by section type

### 4. Comparison Functionality
1. Extract specifications into structured models
2. Compare:
   - Electrical specifications
   - Magnetic specifications
   - Physical specifications
   - Features/Advantages
3. Generate key differences summary
4. Support up to 3 models in comparison

### 5. Implementation Steps
1. Model Migration
   - Move and update models
   - Add validation rules
   - Update imports

2. PDF Processing
   - Port extraction logic
   - Add section classification
   - Implement bullet point detection

3. Vector Store Updates
   - Add metadata support
   - Optimize search
   - Add section type filtering

4. Comparison Service
   - Add comparison logic
   - Implement difference detection
   - Add response formatting

5. API Updates
   - Add comparison endpoints
   - Update query handling
   - Add response models

### Testing Strategy
1. Unit Tests
   - Model validation
   - Section extraction
   - Comparison logic
   - Vector store operations

2. Integration Tests
   - PDF processing pipeline
   - Search functionality
   - Comparison endpoints

3. End-to-End Tests
   - Full PDF upload to comparison workflow
   - Query response accuracy
   - Error handling

## Next Steps
1. Begin with model consolidation
2. Update `models/__init__.py` exports
3. Port PDF processing logic
4. Implement comparison functionality 