"""
CaptionFlow Backend — Configuration
Reads settings from .env file. All values have sensible defaults.
"""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Whisper model — change to "small" for better accuracy (slower)
    whisper_model: str = "base"

    # File storage directories
    upload_dir: str = "uploads"
    output_dir: str = "outputs"
    max_upload_size_mb: int = 500
    temp_file_lifetime_hours: int = 2

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # Frontend URL (for CORS)
    frontend_url: str = "http://localhost:5173"

    # Future Supabase (unused in local MVP)
    supabase_url: str = ""
    supabase_anon_key: str = ""

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Singleton — import this everywhere
settings = Settings()

# Ensure directories exist
Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
Path(settings.output_dir).mkdir(parents=True, exist_ok=True)
