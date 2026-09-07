"""
CaptionFlow — Whisper Transcription Service
Uses OpenAI Whisper (open-source, runs locally, no API key needed).
Model is configurable via WHISPER_MODEL in .env.
"""

import time
import whisper
from typing import Dict, Any, List
from config import settings

# Module-level model cache — load once, reuse.
# This prevents reloading the model on every request (which is slow).
_model = None
_loaded_model_name = None


def _get_model():
    """Load the Whisper model once and cache it in memory."""
    global _model, _loaded_model_name
    model_name = settings.whisper_model

    if _model is None or _loaded_model_name != model_name:
        print(f"[Whisper] Loading model '{model_name}'... (first load may take 30-60s)")
        _model = whisper.load_model(model_name)
        _loaded_model_name = model_name
        print(f"[Whisper] Model '{model_name}' loaded successfully.")

    return _model


def transcribe_audio(audio_path: str) -> Dict[str, Any]:
    """
    Transcribe an audio file using Whisper.
    
    Automatically detects language (Hindi, English, Hinglish, etc.)
    Returns word-level and segment-level timestamps.
    
    Args:
        audio_path: Path to a WAV/MP3/etc audio file
        
    Returns:
        Dict with keys: language, language_probability, segments, duration, model_used
        
    Raises:
        RuntimeError: If transcription fails
        FileNotFoundError: If audio file doesn't exist
    """
    import os
    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    model = _get_model()

    try:
        print(f"[Whisper] Transcribing {audio_path}...")
        start = time.time()

        # Transcribe with word-level timestamps enabled
        # word_timestamps=True gives us per-word timing (used for animations)
        result = model.transcribe(
            audio_path,
            word_timestamps=True,
            verbose=False,
            # Let Whisper auto-detect language:
            language=None,
            # Use beam search for better accuracy (beam_size=5 is default):
            beam_size=5,
            # Best of N samples:
            best_of=5,
            # Temperature — 0 = greedy (fast), higher = more creative:
            temperature=0.0,
            # Condition on previous text for better coherence:
            condition_on_previous_text=True,
            # Compression ratio threshold:
            compression_ratio_threshold=2.4,
            # Log probability threshold:
            logprob_threshold=-1.0,
            # No-speech threshold:
            no_speech_threshold=0.6,
            # Initial prompt helps with Hindi/Hinglish:
            initial_prompt="This audio may contain Hindi, English, or mixed Hindi-English speech.",
        )

        elapsed = time.time() - start
        print(f"[Whisper] Transcription done in {elapsed:.1f}s. Language: {result['language']}")

        # Extract language probability from the first segment if available
        lang_prob = 1.0
        if result.get("segments"):
            # Whisper stores per-segment language info
            first_seg = result["segments"][0]
            if hasattr(first_seg, "get"):
                lang_prob = first_seg.get("avg_logprob", 0.0)
                # avg_logprob is negative; convert to a 0-1 probability estimate
                lang_prob = max(0.0, min(1.0, (lang_prob + 1.0)))

        # Convert segments to our format
        segments = _convert_segments(result["segments"], result["language"])

        # Estimate duration from last segment
        duration = 0.0
        if result["segments"]:
            duration = result["segments"][-1]["end"]

        return {
            "language": result["language"],
            "language_probability": lang_prob,
            "segments": segments,
            "duration": duration,
            "model_used": settings.whisper_model,
            "transcribe_time_seconds": elapsed,
        }

    except Exception as e:
        raise RuntimeError(f"Whisper transcription failed: {str(e)}")


def _convert_segments(raw_segments: list, language: str) -> List[Dict]:
    """Convert Whisper's raw segment output to our internal format."""
    import uuid
    result = []

    for seg in raw_segments:
        # Extract word-level timestamps if available
        words = []
        if "words" in seg:
            for w in seg["words"]:
                words.append({
                    "word": w.get("word", "").strip(),
                    "start": w.get("start", seg["start"]),
                    "end": w.get("end", seg["end"]),
                    "probability": w.get("probability", 1.0),
                })

        result.append({
            "id": str(uuid.uuid4()),
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"].strip(),
            "language": language,
            "words": words if words else None,
        })

    return result
