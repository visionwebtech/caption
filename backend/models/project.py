"""
CaptionFlow — Database Abstraction Layer
In local MVP mode this is a simple in-memory dict.
Later: swap to Supabase by changing the implementation here.
The rest of the codebase doesn't need to change.
"""

from typing import Optional, Dict, Any
from models.caption import ExportStatus


# ─── In-Memory Store (Local MVP) ─────────────────────────────────────────────

_jobs: Dict[str, Dict[str, Any]] = {}


def save_job(job_id: str, data: Dict[str, Any]) -> None:
    """Save or update job metadata."""
    _jobs[job_id] = {**_jobs.get(job_id, {}), **data}


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve job metadata by job_id."""
    return _jobs.get(job_id)


def delete_job(job_id: str) -> None:
    """Remove a job from the store."""
    _jobs.pop(job_id, None)


def update_export_status(job_id: str, status: ExportStatus) -> None:
    """Update the export status for a job."""
    save_job(job_id, {"export_status": status.model_dump()})


def get_export_status(job_id: str) -> Optional[ExportStatus]:
    """Get the export status for a job."""
    job = get_job(job_id)
    if job and "export_status" in job:
        return ExportStatus(**job["export_status"])
    return None


# ─── Future Supabase Tables (Schema Reference) ───────────────────────────────
#
# users:          id, email, created_at, plan
# projects:       id, user_id, title, created_at, updated_at
# videos:         id, project_id, original_filename, storage_path, duration
# captions:       id, video_id, segments (JSONB), language
# caption_styles: id, project_id, style_config (JSONB), preset_name
# exports:        id, project_id, status, output_path, created_at
#
# To connect Supabase:
# 1. Set SUPABASE_URL and SUPABASE_ANON_KEY in .env
# 2. pip install supabase
# 3. Replace the dict above with supabase.table(...).insert/select calls
