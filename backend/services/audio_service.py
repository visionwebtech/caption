"""
CaptionFlow — Audio Extraction Service
Uses FFmpeg to extract audio from the uploaded video as a 16kHz mono WAV.
16kHz mono is the exact format Whisper expects — no re-sampling needed.
"""

import asyncio
import subprocess
import shutil
from pathlib import Path
from utils.file_utils import get_audio_path


def _check_ffmpeg():
    """Raise a clear error if FFmpeg is not installed."""
    if not shutil.which("ffmpeg"):
        raise FileNotFoundError(
            "FFmpeg not found. Please install FFmpeg:\n"
            "  Windows: winget install Gyan.FFmpeg\n"
            "  Then restart your terminal.\n"
            "  Download: https://ffmpeg.org/download.html"
        )


async def extract_audio(job_id: str, video_path: str) -> Path:
    """
    Extract audio from a video file as a 16kHz mono WAV.
    
    Args:
        job_id: Used to name the output audio file
        video_path: Path to the input video file
        
    Returns:
        Path to the extracted WAV file
        
    Raises:
        FileNotFoundError: If FFmpeg is not installed
        RuntimeError: If extraction fails
    """
    _check_ffmpeg()

    audio_path = get_audio_path(job_id)
    
    # FFmpeg command:
    # -i <input>        = input video
    # -vn               = no video (audio only)
    # -acodec pcm_s16le = WAV format (16-bit PCM)
    # -ar 16000         = 16,000 Hz sample rate (Whisper's native rate)
    # -ac 1             = mono channel
    # -y                = overwrite output if exists
    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-vn",
        "-acodec", "pcm_s16le",
        "-ar", "16000",
        "-ac", "1",
        "-y",
        str(audio_path),
    ]

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode("utf-8", errors="replace")
            if "no audio" in error_msg.lower() or "audio stream" in error_msg.lower():
                raise RuntimeError(
                    "No audio track found in the video. "
                    "CaptionFlow requires a video with audio to transcribe."
                )
            raise RuntimeError(
                f"FFmpeg audio extraction failed (exit {proc.returncode}):\n{error_msg}"
            )

        if not audio_path.exists() or audio_path.stat().st_size == 0:
            raise RuntimeError("Audio extraction produced an empty file.")

        return audio_path

    except FileNotFoundError:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected error during audio extraction: {str(e)}")
