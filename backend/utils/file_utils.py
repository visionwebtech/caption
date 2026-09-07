"""
CaptionFlow — File Utilities
Safe, predictable temp file handling. Never executes user-provided filenames.
"""

import uuid
import os
import time
from pathlib import Path
from config import settings


def generate_job_id() -> str:
    """Create a unique job ID (UUID4). Used to name all temp files for a job."""
    return str(uuid.uuid4())


def get_upload_path(job_id: str, extension: str) -> Path:
    """Return a safe upload file path for a given job ID and extension."""
    ext = extension.lstrip(".").lower()
    return Path(settings.upload_dir) / f"{job_id}.{ext}"


def get_audio_path(job_id: str) -> Path:
    """Return the path where extracted audio WAV will be stored."""
    return Path(settings.upload_dir) / f"{job_id}_audio.wav"


def get_output_path(job_id: str) -> Path:
    """Return the path where the final rendered MP4 will be stored."""
    return Path(settings.output_dir) / f"{job_id}_captioned.mp4"


def cleanup_old_files() -> int:
    """
    Delete temp files older than TEMP_FILE_LIFETIME_HOURS.
    Returns the number of files deleted.
    """
    max_age_seconds = settings.temp_file_lifetime_hours * 3600
    now = time.time()
    deleted = 0

    for directory in [settings.upload_dir, settings.output_dir]:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
        for file in dir_path.iterdir():
            if file.is_file():
                age = now - file.stat().st_mtime
                if age > max_age_seconds:
                    try:
                        file.unlink()
                        deleted += 1
                    except Exception:
                        pass

    return deleted


def delete_job_files(job_id: str) -> None:
    """Delete all files associated with a specific job ID."""
    for directory in [settings.upload_dir, settings.output_dir]:
        dir_path = Path(directory)
        if not dir_path.exists():
            continue
        for file in dir_path.glob(f"{job_id}*"):
            try:
                file.unlink()
            except Exception:
                pass


# Allowed video MIME types and extensions
ALLOWED_EXTENSIONS = {".mp4", ".mov", ".avi", ".webm", ".mkv", ".m4v"}
ALLOWED_MIME_TYPES = {
    "video/mp4",
    "video/quicktime",
    "video/x-msvideo",
    "video/webm",
    "video/x-matroska",
    "video/x-m4v",
}


def is_allowed_video(filename: str, content_type: str) -> bool:
    """
    Validate that the file is a supported video format.
    Checks both extension and MIME type.
    """
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS and content_type in ALLOWED_MIME_TYPES
