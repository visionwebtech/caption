"""
CaptionFlow — Pydantic Data Models
These are the shared data structures used across routes and services.
Pydantic automatically validates all data (wrong types raise clear errors).
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from enum import Enum


# ─── Caption Segment ──────────────────────────────────────────────────────────

class CaptionSegment(BaseModel):
    """A single caption block shown on screen."""
    id: str
    start: float = Field(..., ge=0, description="Start time in seconds")
    end: float = Field(..., ge=0, description="End time in seconds")
    text: str = Field(..., min_length=1, max_length=500)
    language: Optional[str] = None  # e.g. "hi", "en"
    words: Optional[List["WordTimestamp"]] = None  # word-level timestamps

    @field_validator("end")
    @classmethod
    def end_must_be_after_start(cls, v, info):
        start = info.data.get("start", 0)
        if v <= start:
            raise ValueError(f"end ({v}) must be greater than start ({start})")
        return v


class WordTimestamp(BaseModel):
    """Word-level timestamp from Whisper (used for word highlight animations)."""
    word: str
    start: float
    end: float
    probability: Optional[float] = None


# ─── Style Settings ───────────────────────────────────────────────────────────

class TextAlignment(str, Enum):
    left = "left"
    center = "center"
    right = "right"


class AnimationType(str, Enum):
    none = "none"
    fade = "fade"
    pop = "pop"
    scale = "scale"
    slide_up = "slide_up"
    slide_down = "slide_down"
    word_pop = "word_pop"
    word_highlight = "word_highlight"
    type_reveal = "type_reveal"


class CaptionStyle(BaseModel):
    """Full styling configuration for captions."""
    preset_name: Optional[str] = "Custom"

    # Font
    font_family: str = "Poppins"
    font_size: int = Field(default=36, ge=12, le=120)
    font_weight: str = "700"  # "400", "600", "700", "800", "900"
    
    # Colors
    text_color: str = "#FFFFFF"
    highlight_color: str = "#FFD700"
    
    # Background (caption box)
    background_enabled: bool = False
    background_color: str = "#000000"
    background_opacity: float = Field(default=0.6, ge=0.0, le=1.0)
    background_padding: int = Field(default=8, ge=0, le=50)
    border_radius: int = Field(default=8, ge=0, le=50)
    
    # Outline
    outline_enabled: bool = True
    outline_color: str = "#000000"
    outline_thickness: int = Field(default=2, ge=0, le=10)
    
    # Shadow
    shadow_enabled: bool = False
    shadow_color: str = "#000000"
    shadow_intensity: float = Field(default=0.5, ge=0.0, le=1.0)
    shadow_offset_x: int = Field(default=2, ge=-20, le=20)
    shadow_offset_y: int = Field(default=2, ge=-20, le=20)
    
    # Position
    vertical_position: float = Field(default=0.85, ge=0.0, le=1.0)
    horizontal_alignment: TextAlignment = TextAlignment.center
    max_chars_per_line: int = Field(default=40, ge=10, le=100)
    
    # Typography
    line_spacing: float = Field(default=1.4, ge=0.8, le=3.0)
    letter_spacing: int = Field(default=0, ge=-5, le=20)
    
    # Animation
    animation: AnimationType = AnimationType.fade
    word_highlight_enabled: bool = False
    word_highlight_color: str = "#FF6B35"


# ─── Transcription ────────────────────────────────────────────────────────────

class TranscriptionResult(BaseModel):
    """Result returned from the Whisper transcription service."""
    job_id: str
    language: str
    language_probability: float
    segments: List[CaptionSegment]
    duration_seconds: float
    model_used: str


# ─── Upload ───────────────────────────────────────────────────────────────────

class UploadResponse(BaseModel):
    """Response after successfully uploading a video."""
    job_id: str
    filename: str
    size_bytes: int
    duration_seconds: Optional[float] = None
    message: str = "Upload successful"


# ─── Export ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    """Request body for starting a video render."""
    job_id: str
    segments: List[CaptionSegment]
    style: CaptionStyle


class ExportStatus(BaseModel):
    """Current status of an export job."""
    job_id: str
    status: str  # "queued", "processing", "done", "error"
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    message: str = ""
    download_url: Optional[str] = None
    file_size_bytes: Optional[int] = None


# ─── Error ────────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """Standardized error response."""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None


# Allow forward references (WordTimestamp used in CaptionSegment)
CaptionSegment.model_rebuild()
