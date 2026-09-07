"""
CaptionFlow — Captions Route
CRUD operations for caption segments, plus split/merge.
"""

from fastapi import APIRouter, HTTPException
from typing import List
from models.caption import CaptionSegment
from models.project import get_job, save_job
import uuid

router = APIRouter(prefix="/api/captions", tags=["captions"])


def _get_segments(job_id: str) -> List[CaptionSegment]:
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    transcription = job.get("transcription")
    if not transcription:
        raise HTTPException(status_code=400, detail="No transcription found. Please transcribe first.")
    return [CaptionSegment(**s) for s in transcription["segments"]]


def _save_segments(job_id: str, segments: List[CaptionSegment]):
    job = get_job(job_id)
    transcription = job.get("transcription", {})
    transcription["segments"] = [s.model_dump() for s in segments]
    save_job(job_id, {"transcription": transcription})


@router.get("/{job_id}", response_model=List[CaptionSegment])
async def get_captions(job_id: str):
    """Get all caption segments for a job."""
    return _get_segments(job_id)


@router.put("/{job_id}", response_model=List[CaptionSegment])
async def update_captions(job_id: str, segments: List[CaptionSegment]):
    """Replace all caption segments (full update after editing)."""
    if not get_job(job_id):
        raise HTTPException(status_code=404, detail="Job not found.")
    _save_segments(job_id, segments)
    return segments


@router.delete("/{job_id}/{segment_id}", response_model=List[CaptionSegment])
async def delete_segment(job_id: str, segment_id: str):
    """Delete a single caption segment by ID."""
    segments = _get_segments(job_id)
    new_segments = [s for s in segments if s.id != segment_id]
    if len(new_segments) == len(segments):
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found.")
    _save_segments(job_id, new_segments)
    return new_segments


@router.post("/{job_id}/split/{segment_id}", response_model=List[CaptionSegment])
async def split_segment(job_id: str, segment_id: str, split_time: float):
    """
    Split a caption segment at a given time.
    The segment is divided into two at split_time.
    """
    segments = _get_segments(job_id)
    result = []
    split_done = False
    for seg in segments:
        if seg.id == segment_id and not split_done:
            if not (seg.start < split_time < seg.end):
                raise HTTPException(
                    status_code=400,
                    detail=f"split_time {split_time} is outside segment range [{seg.start}, {seg.end}]",
                )
            # Find approximate midpoint in text
            words = seg.text.split()
            mid = max(1, len(words) // 2)
            first_text = " ".join(words[:mid])
            second_text = " ".join(words[mid:])
            result.append(CaptionSegment(
                id=str(uuid.uuid4()),
                start=seg.start,
                end=split_time,
                text=first_text or seg.text,
                language=seg.language,
            ))
            result.append(CaptionSegment(
                id=str(uuid.uuid4()),
                start=split_time,
                end=seg.end,
                text=second_text or seg.text,
                language=seg.language,
            ))
            split_done = True
        else:
            result.append(seg)

    if not split_done:
        raise HTTPException(status_code=404, detail=f"Segment '{segment_id}' not found.")

    _save_segments(job_id, result)
    return result


@router.post("/{job_id}/merge", response_model=List[CaptionSegment])
async def merge_segments(job_id: str, segment_ids: List[str]):
    """
    Merge two or more adjacent segments into one.
    Text is joined, timing spans from first to last.
    """
    if len(segment_ids) < 2:
        raise HTTPException(status_code=400, detail="Need at least 2 segment IDs to merge.")

    segments = _get_segments(job_id)
    id_set = set(segment_ids)
    to_merge = [s for s in segments if s.id in id_set]

    if len(to_merge) != len(segment_ids):
        raise HTTPException(status_code=404, detail="One or more segment IDs not found.")

    to_merge_sorted = sorted(to_merge, key=lambda s: s.start)
    merged = CaptionSegment(
        id=str(uuid.uuid4()),
        start=to_merge_sorted[0].start,
        end=to_merge_sorted[-1].end,
        text=" ".join(s.text for s in to_merge_sorted),
        language=to_merge_sorted[0].language,
    )

    # Rebuild list in order, replacing merged segments with one merged segment
    first_idx = next(i for i, s in enumerate(segments) if s.id == to_merge_sorted[0].id)
    new_segments = [s for s in segments if s.id not in id_set]
    new_segments.insert(first_idx, merged)
    new_segments.sort(key=lambda s: s.start)

    _save_segments(job_id, new_segments)
    return new_segments
