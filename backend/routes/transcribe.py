"""
CaptionFlow — Transcription Route
Runs Whisper on the uploaded video's audio and returns caption segments.
"""

import asyncio
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
import json

from models.caption import TranscriptionResult, ErrorResponse
from models.project import get_job, save_job
from services.audio_service import extract_audio
from services.transcription_service import transcribe_audio
from services.caption_service import build_caption_segments

router = APIRouter(prefix="/api/transcribe", tags=["transcription"])


@router.post("/{job_id}", response_model=TranscriptionResult)
async def transcribe_video(job_id: str):
    """
    Transcribe audio from a previously uploaded video.
    Steps: extract audio → run Whisper → segment captions → return.
    """
    # 1. Verify job exists
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found. Please upload first.")

    video_path = job.get("video_path")
    if not video_path:
        raise HTTPException(status_code=400, detail="No video path found for this job.")

    # 2. Extract audio
    try:
        audio_path = await extract_audio(job_id, video_path)
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio extraction failed: {str(e)}")

    # 3. Transcribe with Whisper
    try:
        raw_result = await asyncio.get_event_loop().run_in_executor(
            None, transcribe_audio, str(audio_path)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    # 4. Build caption segments
    segments = build_caption_segments(raw_result["segments"], raw_result["language"])

    # 5. Build and save result
    result = TranscriptionResult(
        job_id=job_id,
        language=raw_result["language"],
        language_probability=raw_result.get("language_probability", 1.0),
        segments=segments,
        duration_seconds=raw_result.get("duration", 0.0),
        model_used=raw_result.get("model_used", "base"),
    )

    save_job(job_id, {
        "transcription": result.model_dump(),
        "language": result.language,
    })

    return result


@router.get("/{job_id}/stream")
async def transcribe_stream(job_id: str):
    """
    SSE endpoint that streams transcription progress updates to the frontend.
    The frontend listens to this and updates its progress bar in real-time.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")

    async def event_generator():
        steps = [
            (10, "Extracting audio from video..."),
            (30, "Loading Whisper model..."),
            (50, "Transcribing speech... (this may take a moment)"),
            (80, "Building caption segments..."),
            (100, "Transcription complete!"),
        ]
        for progress, message in steps:
            data = json.dumps({"progress": progress, "message": message})
            yield f"data: {data}\n\n"
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
