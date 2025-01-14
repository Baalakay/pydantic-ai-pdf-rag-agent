from typing import List
from pydantic import Field
from .base import BaseDocument

class FeatureSet(BaseDocument):
    """Model representing a set of features and advantages extracted from a PDF."""
    features: List[str] = Field(default_factory=list, description="List of extracted features")
    advantages: List[str] = Field(default_factory=list, description="List of extracted advantages")
    source_file: str = Field(..., description="Original PDF filename")
