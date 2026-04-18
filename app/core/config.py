"""Application Configuration"""
import os
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
    
    # Gemini API
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "")
    
    # File handling
    MAX_FILE_SIZE_MB: int = int(os.getenv("MAX_FILE_SIZE_MB", "10"))
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "outputs/uploads")
    REPORT_DIR: str = os.getenv("REPORT_DIR", "outputs/reports")
    
    # Cleanup
    CLEANUP_HOURS: int = int(os.getenv("CLEANUP_HOURS", "24"))
    
    # Database
    DB_PATH: str = os.getenv("DB_PATH", "outputs/medextract.db")

    # Supported file types
    ALLOWED_EXTENSIONS: set = {".pdf", ".docx", ".txt"}
    
    API_BASE_URL: str = os.getenv("API_BASE_URL", "http://localhost:8000")

    class Config:
        env_file = ".env"
        extra = "ignore"  # Ignore extra environment variables not defined in the model


settings = Settings()
