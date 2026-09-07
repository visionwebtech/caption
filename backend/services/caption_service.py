"""
CaptionFlow — Caption Segmentation Engine
Converts raw Whisper output into short, readable caption segments.

Rules:
- Max ~40 characters per line (configurable)
- Max 2 lines on screen
- Break at natural phrase boundaries (punctuation, pauses)
- Keep Hindi Unicode intact
- Never split a word mid-character
"""

import re
import uuid
from typing import List, Dict, Any
from models.caption import CaptionSegment


# Languages that use non-Latin scripts — need special word-splitting logic
NON_LATIN_LANGUAGES = {"hi", "mr", "ne", "pa", "gu", "ur", "ar", "zh", "ja", "ko"}

# Max characters per caption line (two lines = 2x this)
DEFAULT_MAX_CHARS = 40
# Max words per caption segment
DEFAULT_MAX_WORDS = 8
# Min duration for a caption segment (seconds)
MIN_SEGMENT_DURATION = 0.5


def build_caption_segments(
    raw_segments: List[Dict[str, Any]],
    language: str,
    max_chars: int = DEFAULT_MAX_CHARS,
    max_words: int = DEFAULT_MAX_WORDS,
) -> List[CaptionSegment]:
    """
    Convert Whisper segments into short, display-ready caption segments.
    
    Args:
        raw_segments: Raw Whisper output segments
        language: Detected language code (e.g., "hi", "en")
        max_chars: Max characters per line
        max_words: Max words per caption segment
        
    Returns:
        List of CaptionSegment ready for display
    """
    if not raw_segments:
        return []

    all_captions = []

    for seg in raw_segments:
        text = seg.get("text", "").strip()
        if not text:
            continue

        start = seg.get("start", 0.0)
        end = seg.get("end", start + 1.0)
        words_data = seg.get("words") or []

        if end <= start:
            end = start + MIN_SEGMENT_DURATION

        # If we have word-level timestamps, use them for accurate splitting
        if words_data:
            chunks = _split_with_word_timestamps(
                words_data, language, max_chars, max_words
            )
        else:
            # Fall back to time-based splitting
            chunks = _split_by_text(text, start, end, language, max_chars, max_words)

        all_captions.extend(chunks)

    # Sort by start time and fix any overlaps
    all_captions.sort(key=lambda s: s.start)
    all_captions = _fix_overlaps(all_captions)

    return all_captions


def _split_with_word_timestamps(
    words_data: List[Dict],
    language: str,
    max_chars: int,
    max_words: int,
) -> List[CaptionSegment]:
    """Split using word-level timestamps from Whisper for precise timing."""
    if not words_data:
        return []

    segments = []
    current_words = []
    current_chars = 0

    for i, word_info in enumerate(words_data):
        word = word_info.get("word", "").strip()
        if not word:
            continue

        word_len = len(word)
        space = 1 if current_words else 0

        # Check if adding this word would exceed limits
        would_exceed_chars = (current_chars + space + word_len) > (max_chars * 2)
        would_exceed_words = len(current_words) >= max_words
        is_phrase_break = _is_phrase_break(word)

        # Flush current segment if limits exceeded or natural break detected
        if current_words and (would_exceed_chars or would_exceed_words or is_phrase_break):
            seg = _make_segment(current_words, language)
            if seg:
                segments.append(seg)
            current_words = []
            current_chars = 0

        current_words.append(word_info)
        current_chars += space + word_len

    # Flush remaining words
    if current_words:
        seg = _make_segment(current_words, language)
        if seg:
            segments.append(seg)

    return segments


def _make_segment(words_data: List[Dict], language: str) -> CaptionSegment | None:
    """Create a CaptionSegment from a list of word timestamp dicts."""
    if not words_data:
        return None

    text = " ".join(w.get("word", "").strip() for w in words_data)
    text = text.strip()

    if not text:
        return None

    start = words_data[0].get("start", 0.0)
    end = words_data[-1].get("end", start + MIN_SEGMENT_DURATION)

    if end <= start:
        end = start + MIN_SEGMENT_DURATION

    return CaptionSegment(
        id=str(uuid.uuid4()),
        start=start,
        end=end,
        text=text,
        language=language,
    )


def _split_by_text(
    text: str,
    start: float,
    end: float,
    language: str,
    max_chars: int,
    max_words: int,
) -> List[CaptionSegment]:
    """
    Split text into caption segments by character/word count.
    Used when word-level timestamps are unavailable.
    Time is distributed proportionally.
    """
    # Split at sentence boundaries first
    sentences = re.split(r'(?<=[।.!?])\s+', text)
    sentences = [s.strip() for s in sentences if s.strip()]

    all_chunks = []
    for sentence in sentences:
        words = sentence.split()
        chunk_words = []
        chunk_chars = 0

        for word in words:
            space = 1 if chunk_words else 0
            if chunk_words and (chunk_chars + space + len(word) > max_chars * 2 or len(chunk_words) >= max_words):
                all_chunks.append(" ".join(chunk_words))
                chunk_words = [word]
                chunk_chars = len(word)
            else:
                chunk_words.append(word)
                chunk_chars += space + len(word)

        if chunk_words:
            all_chunks.append(" ".join(chunk_words))

    if not all_chunks:
        all_chunks = [text]

    # Distribute time proportionally across chunks
    total_chars = sum(len(c) for c in all_chunks)
    duration = end - start
    segments = []
    current_start = start

    for i, chunk in enumerate(all_chunks):
        is_last = (i == len(all_chunks) - 1)
        if is_last:
            chunk_end = end
        else:
            ratio = len(chunk) / total_chars if total_chars > 0 else 1.0 / len(all_chunks)
            chunk_end = current_start + (duration * ratio)
            chunk_end = min(chunk_end, end - MIN_SEGMENT_DURATION * (len(all_chunks) - i - 1))

        if chunk_end <= current_start:
            chunk_end = current_start + MIN_SEGMENT_DURATION

        segments.append(CaptionSegment(
            id=str(uuid.uuid4()),
            start=round(current_start, 3),
            end=round(chunk_end, 3),
            text=chunk,
            language=language,
        ))
        current_start = chunk_end

    return segments


def _is_phrase_break(word: str) -> bool:
    """Detect if a word ends with punctuation that signals a phrase boundary."""
    return bool(re.search(r'[।.!?,;:\-–—]$', word.strip()))


def _fix_overlaps(segments: List[CaptionSegment]) -> List[CaptionSegment]:
    """Ensure no two caption segments overlap in time."""
    for i in range(1, len(segments)):
        prev = segments[i - 1]
        curr = segments[i]
        if curr.start < prev.end:
            # Push current start to just after previous end
            new_start = round(prev.end + 0.05, 3)
            if new_start >= curr.end:
                new_start = curr.end - MIN_SEGMENT_DURATION
            segments[i] = CaptionSegment(
                id=curr.id,
                start=new_start,
                end=curr.end,
                text=curr.text,
                language=curr.language,
                words=curr.words,
            )
    return segments
