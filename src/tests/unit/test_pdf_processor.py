"""Tests for PDF processor."""
import pytest
from unittest.mock import Mock, patch
from hsi_pdf_agent.core.process_pdf import PDFProcessor
from hsi_pdf_agent.models.pdf import PDFData
from hsi_pdf_agent.core.config import get_settings
from typing import List, cast
from pathlib import Path 