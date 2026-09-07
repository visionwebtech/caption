"""
CaptionFlow — Export Route
Triggers FFmpeg render and streams progress via SSE.
"""

import asyncio
import json
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pathlib import Path

from models.caption import ExportRequest, ExportStatus, ErrorResponse
from models.project import get_job, save_job, update_export_status, get_export_status
from services.render_service import render_video
from utils.file_utils import get_output_path

router = APIRouter(prefix="/api/export", tags=["export"])


@router.post("/{job_id}/start")
async def start_export(job_id: str, request: ExportRequest, background_tasks: BackgroundTasks):
    """
    Start a background render job.
    Returns immediately — poll /status or /progress for updates.
    """
    if not get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")

    # Set initial status
    status = ExportStatus(job_id=job_id, status="queued", progress=0.0, message="Render queued...")
    update_export_status(job_id, status)

    # Run render in background
    background_tasks.add_task(_run_render, job_id, request)

    return {"job_id": job_id, "status": "queued", "message": "Render started."}


async def _run_render(job_id: str, request: ExportRequest):
    """Background task: render video with captions."""
    try:
        update_export_status(job_id, ExportStatus(
            job_id=job_id, status="processing", progress=10.0,
            message="Starting render..."
        ))
        job = get_job(job_id)
        video_path = job["video_path"]
        output_path = get_output_path(job_id)

        await render_video(
            job_id=job_id,
            input_video=video_path,
            output_path=str(output_path),
            segments=request.segments,
            style=request.style,
            progress_callback=lambda p, m: update_export_status(
                job_id, ExportStatus(job_id=job_id, status="processing", progress=p, message=m)
            ),
        )

        file_size = output_path.stat().st_size if output_path.exists() else 0
        update_export_status(job_id, ExportStatus(
            job_id=job_id, status="done", progress=100.0,
            message="Render complete!",
            download_url=f"/api/export/{job_id}/download",
            file_size_bytes=file_size,
        ))

    except Exception as e:
        update_export_status(job_id, ExportStatus(
            job_id=job_id, status="error", progress=0.0,
            message=f"Render failed: {str(e)}"
        ))


@router.get("/{job_id}/status", response_model=ExportStatus)
async def get_status(job_id: str):
    """Poll this endpoint to get the current render status."""
    status = get_export_status(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="No export job found.")
    return status


@router.get("/{job_id}/progress")
async def stream_progress(job_id: str):
    """
    SSE endpoint — the frontend connects here and gets live progress updates.
    Closes automatically when rendering is done or errors.
    """
    async def generator():
        while True:
            status = get_export_status(job_id)
            if status:
                data = json.dumps(status.model_dump())
                yield f"data: {data}\n\n"
                if status.status in ("done", "error"):
                    break
            else:
                yield f"data: {json.dumps({'status': 'waiting'})}\n\n"
            await asyncio.sleep(1)

    return StreamingResponse(generator(), media_type="text/event-stream")


@router.get("/{job_id}/download")
async def download_video(job_id: str):
    """Download the rendered MP4 file."""
    output_path = get_output_path(job_id)
    if not output_path.exists():
        raise HTTPException(status_code=404, detail="Rendered video not found. Please render first.")

    status = get_export_status(job_id)
    if not status or status.status != "done":
        raise HTTPException(status_code=400, detail="Video is not ready yet.")

    return FileResponse(
        path=str(output_path),
        media_type="video/mp4",
        filename="captionflow_export.mp4",
    )
