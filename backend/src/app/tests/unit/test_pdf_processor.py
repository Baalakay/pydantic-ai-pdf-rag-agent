import pytest
from unittest.mock import Mock, patch
from backend.src.app.core.process_pdf import PDFProcessor
from backend.src.app.models.pdf import PDFData
from backend.src.app.core.config import get_settings
from typing import List, cast
from pathlib import Path 