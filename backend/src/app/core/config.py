"""Application configuration using Pydantic Settings management."""
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings.

    Attributes:
        BASE_DIR: Base directory for the application
        UPLOADS_DIR: Directory for uploaded files
        PDF_DIR: Directory for PDF files
        DIAGRAMS_DIR: Directory for diagram files
        VECTOR_STORE_DIR: Directory for vector store data
    """
    model_config = SettingsConfigDict(
        env_prefix="APP_",
        case_sensitive=False,
        extra="forbid"
    )

    # Base directory is one level up from this file
    BASE_DIR: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.resolve()

    # Configurable paths with defaults relative to BASE_DIR
    UPLOADS_DIR: Path = Field(
        default_factory=lambda: Settings.BASE_DIR / "data",
        description="Directory for uploaded files"
    )

    @computed_field
    def PDF_DIR(self) -> Path:
        """Get PDF directory and ensure it exists."""
        pdf_dir = self.UPLOADS_DIR / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return pdf_dir

    @computed_field
    def DIAGRAMS_DIR(self) -> Path:
        """Get diagrams directory and ensure it exists."""
        diagrams_dir = self.UPLOADS_DIR / "diagrams"
        diagrams_dir.mkdir(parents=True, exist_ok=True)
        return diagrams_dir

    @computed_field
    def VECTOR_STORE_DIR(self) -> Path:
        """Get vector store directory and ensure it exists."""
        vector_store_dir = self.UPLOADS_DIR / "vector_store"
        vector_store_dir.mkdir(parents=True, exist_ok=True)
        return vector_store_dir

    def model_post_init(self, context: Any) -> None:
        """Ensure upload directory exists and is absolute."""
        self.UPLOADS_DIR = self.UPLOADS_DIR.resolve()
        self.UPLOADS_DIR.mkdir(exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
