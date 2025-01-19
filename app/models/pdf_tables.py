from typing import List, Dict, Any
from pydantic import BaseModel, Field

class Table(BaseModel):
    """Represents a table extracted from a PDF."""
    data: List[Dict[str, Any]] = Field(default_factory=list)

class PDFTables(BaseModel):
    """Model for storing tables and specifications extracted from a PDF."""
    tables: List[Table] = Field(default_factory=list)
    specs: List[Dict[str, Any]] = Field(default_factory=list)
    features_advantages: Dict[str, List[str]] = Field(default_factory=dict)