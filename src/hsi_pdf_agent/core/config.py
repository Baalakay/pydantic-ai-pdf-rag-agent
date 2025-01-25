"""Application configuration using Pydantic Settings management."""
from functools import lru_cache
from pathlib import Path
from typing import ClassVar, Any

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings.

    Attributes:
        BASE_DIR: Base directory for the application (workspace root)
        DATA_DIR: Directory for application data files
        PDF_DIR: Directory for PDF files
        DIAGRAMS_DIR: Directory for diagram files
        FRONTEND_PUBLIC_DIR: Directory for frontend public static assets
        FRONTEND_DIAGRAMS_DIR: Directory for frontend diagram files
        admin_username: Username for admin access
        admin_password_hash: Hashed password for admin access
        secret_key: Secret key for JWT token generation
        token_expire_minutes: JWT token expiration time in minutes
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields from .env
    )

    # Base directory is the workspace root
    BASE_DIR: ClassVar[Path] = Path(__file__).parent.parent.parent.parent.resolve()

    # Admin settings
    ADMIN_USERNAME: str = Field(
        default="admin",
        description="Username for admin access"
    )
    ADMIN_PASSWORD_HASH: str = Field(
        default="$argon2id$v=19$m=65536,t=3,p=4$XrsNRWLF9AYlg4hq9R58vQ$BtQgOdhy/8rwMWOTBkHvTx5OEqTKtSPX6JCUagMsQxg",
        description="Hashed password for admin access"
    )
    SECRET_KEY: str = Field(
        default="your-secret-key",
        description="Secret key for JWT token generation"
    )
    token_expire_minutes: int = Field(
        default=30,
        description="JWT token expiration time in minutes"
    )

    # Frontend settings
    VITE_FRONTEND_PORT: str = Field(
        default="5173",
        description="Frontend development server port"
    )
    VITE_API_URL: str = Field(
        default="http://localhost:8000",
        description="Backend API URL for frontend"
    )

    # Python path
    PYTHONPATH: str = Field(
        default_factory=lambda: str(Settings.BASE_DIR),
        description="Python path for the application"
    )

    # Configurable paths with defaults relative to BASE_DIR
    DATA_DIR: Path = Field(
        default_factory=lambda: Settings.BASE_DIR / "data",
        description="Directory for application data files"
    )

    @computed_field
    def PROJECT_ROOT(self) -> Path:
        """Get the project root directory."""
        return self.BASE_DIR

    @computed_field
    def PDF_DIR(self) -> Path:
        """Get PDF directory and ensure it exists."""
        pdf_dir = self.DATA_DIR / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        return pdf_dir

    @computed_field
    def DIAGRAMS_DIR(self) -> Path:
        """Get diagrams directory and ensure it exists."""
        diagrams_dir = self.FRONTEND_PUBLIC_DIR / "diagrams"
        diagrams_dir.mkdir(parents=True, exist_ok=True)
        return diagrams_dir

    @computed_field
    def FRONTEND_PUBLIC_DIR(self) -> Path:
        """Get frontend public directory for static assets."""
        public_dir = self.BASE_DIR / "frontend" / "public"
        public_dir.mkdir(parents=True, exist_ok=True)
        return public_dir

    def model_post_init(self, context: Any) -> None:
        """Ensure data directory exists and is absolute."""
        self.DATA_DIR = self.DATA_DIR.resolve()
        self.DATA_DIR.mkdir(exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Create a global settings instance
settings = get_settings()
