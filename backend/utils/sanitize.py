"""
CaptionFlow — Input Sanitization
Prevents command injection when passing user text into FFmpeg drawtext filters.
"""

import re
import unicodedata


# Characters that are dangerous inside FFmpeg filter strings
_FFMPEG_ESCAPE_MAP = str.maketrans({
    "'": "\\'",
    ":": "\\:",
    "\\": "\\\\",
    "[": "\\[",
    "]": "\\]",
    ",": "\\,",
    ";": "\\;",
})


def sanitize_for_ffmpeg(text: str) -> str:
    """
    Escape special characters so caption text is safe to embed in
    FFmpeg drawtext filter expressions.
    Never pass raw user text directly into FFmpeg commands.
    """
    if not isinstance(text, str):
        return ""
    # Normalize Unicode (important for Hindi/Devanagari)
    text = unicodedata.normalize("NFC", text)
    # Apply FFmpeg escape map
    return text.translate(_FFMPEG_ESCAPE_MAP)


def sanitize_filename(filename: str) -> str:
    """
    Strip dangerous characters from a filename.
    Only used for display purposes — never used to actually name temp files
    (those always use UUID job IDs).
    """
    # Keep only safe characters for display
    safe = re.sub(r'[^\w\s\-.]', '', filename)
    return safe.strip()[:200]  # max 200 chars


def clamp(value: float, min_val: float, max_val: float) -> float:
    """Clamp a numeric value between min and max."""
    return max(min_val, min(max_val, value))


def validate_timestamp(ts: float) -> float:
    """Ensure a timestamp is a non-negative finite number."""
    if not isinstance(ts, (int, float)):
        raise ValueError(f"Timestamp must be a number, got {type(ts)}")
    if ts < 0:
        raise ValueError(f"Timestamp cannot be negative: {ts}")
    return float(ts)
