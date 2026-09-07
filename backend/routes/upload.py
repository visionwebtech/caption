"""
CaptionFlow — Upload Route
Handles video file upload with full validation.
"""

import os
import aiofiles
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse

from config import settings
from models.caption import UploadResponse, ErrorResponse
from models.project import save_job
from utils.file_utils import (
    generate_job_id,
    get_upload_path,
    is_allowed_video,
    ALLOWED_EXTENSIONS,
)

router = APIRouter(prefix="/api/upload", tags=["upload"])

MAX_BYTES = settings.max_upload_size_mb * 1024 * 1024


@router.post("", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """
    Upload a video file.
    - Validates file type and size
    - Saves to a safe temp location with a UUID filename
    - Returns a job_id used for all subsequent operations
    """
    # 1. Validate file type
    if not is_allowed_video(file.filename or "", file.content_type or ""):
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{file.content_type}'. "
                   f"Allowed extensions: {allowed}",
        )

    # 2. Generate a unique job ID (never use the original filename for storage)
    job_id = generate_job_id()
    ext = os.path.splitext(file.filename or "video.mp4")[1].lower() or ".mp4"
    upload_path = get_upload_path(job_id, ext)

    # 3. Stream file to disk while checking size limit
    total_bytes = 0
    try:
        async with aiofiles.open(upload_path, "wb") as out_file:
            while True:
                chunk = await file.read(1024 * 1024)  # read 1 MB at a time
                if not chunk:
                    break
                total_bytes += len(chunk)
                if total_bytes > MAX_BYTES:
                    # Delete partial file and reject
                    await out_file.close()
                    upload_path.unlink(missing_ok=True)
                    raise HTTPException(
                        status_code=413,
                        detail=f"File too large. Maximum allowed size is "
                               f"{settings.max_upload_size_mb} MB.",
                    )
                await out_file.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        upload_path.unlink(missing_ok=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

    # 4. Save job metadata
    save_job(job_id, {
        "original_filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": total_bytes,
        "video_path": str(upload_path),
        "ext": ext,
    })

    return UploadResponse(
        job_id=job_id,
        filename=file.filename or "video",
        size_bytes=total_bytes,
        message="Upload successful. Ready to transcribe.",
    )
