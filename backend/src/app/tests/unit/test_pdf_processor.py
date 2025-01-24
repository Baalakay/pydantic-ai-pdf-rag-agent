"""Tests for PDF processor."""
import pytest
from unittest.mock import Mock, patch
from ...core.process_pdf import PDFProcessor
from ...models.pdf import PDFData
from ...core.config import get_settings
from typing import List, cast
from pathlib import Path 