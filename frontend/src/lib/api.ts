/**
 * CaptionFlow — Backend API Client
 * All backend calls go through here. Never scatter fetch() calls in components.
 */

import axios from 'axios';
import type {
  UploadResponse,
  TranscriptionResult,
  CaptionSegment,
  CaptionStyle,
  ExportStatus,
} from '../types';

// In development: Vite proxies /api → http://localhost:8000
const API_BASE = '/api';

const client = axios.create({
  baseURL: API_BASE,
  timeout: 300_000, // 5 minutes (video processing can be slow)
});

// ─── Error Handler ────────────────────────────────────────────────────────────

function handleError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const msg =
      error.response?.data?.detail ||
      error.response?.data?.error ||
      error.message ||
      'Unknown error';
    throw new Error(msg);
  }
  throw error;
}

// ─── Health ───────────────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{
  status: string;
  whisper_model: string;
  ffmpeg_available: boolean;
}> {
  try {
    const res = await client.get('/health');
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

// ─── Upload ───────────────────────────────────────────────────────────────────

export async function uploadVideo(
  file: File,
  onProgress?: (percent: number) => void
): Promise<UploadResponse> {
  try {
    const formData = new FormData();
    formData.append('file', file);

    const res = await client.post<UploadResponse>('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (event) => {
        if (event.total && onProgress) {
          onProgress(Math.round((event.loaded / event.total) * 100));
        }
      },
    });
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

// ─── Transcription ────────────────────────────────────────────────────────────

export async function transcribeVideo(jobId: string): Promise<TranscriptionResult> {
  try {
    const res = await client.post<{
      job_id: string;
      language: string;
      language_probability: number;
      segments: CaptionSegment[];
      duration_seconds: number;
      model_used: string;
    }>(`/transcribe/${jobId}`);

    return {
      jobId: res.data.job_id,
      language: res.data.language,
      languageProbability: res.data.language_probability,
      segments: res.data.segments,
      durationSeconds: res.data.duration_seconds,
      modelUsed: res.data.model_used,
    };
  } catch (e) {
    return handleError(e);
  }
}

// ─── Captions ────────────────────────────────────────────────────────────────

export async function getCaptions(jobId: string): Promise<CaptionSegment[]> {
  try {
    const res = await client.get<CaptionSegment[]>(`/captions/${jobId}`);
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

export async function updateCaptions(
  jobId: string,
  segments: CaptionSegment[]
): Promise<CaptionSegment[]> {
  try {
    const res = await client.put<CaptionSegment[]>(`/captions/${jobId}`, segments);
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

export async function deleteSegment(
  jobId: string,
  segmentId: string
): Promise<CaptionSegment[]> {
  try {
    const res = await client.delete<CaptionSegment[]>(`/captions/${jobId}/${segmentId}`);
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

export async function splitSegment(
  jobId: string,
  segmentId: string,
  splitTime: number
): Promise<CaptionSegment[]> {
  try {
    const res = await client.post<CaptionSegment[]>(
      `/captions/${jobId}/split/${segmentId}`,
      null,
      { params: { split_time: splitTime } }
    );
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

export async function mergeSegments(
  jobId: string,
  segmentIds: string[]
): Promise<CaptionSegment[]> {
  try {
    const res = await client.post<CaptionSegment[]>(
      `/captions/${jobId}/merge`,
      segmentIds
    );
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

// ─── Export ───────────────────────────────────────────────────────────────────

export async function startExport(
  jobId: string,
  segments: CaptionSegment[],
  style: CaptionStyle
): Promise<{ job_id: string; status: string }> {
  try {
    const res = await client.post(`/export/${jobId}/start`, {
      job_id: jobId,
      segments,
      style,
    });
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

export async function getExportStatus(jobId: string): Promise<ExportStatus> {
  try {
    const res = await client.get<ExportStatus>(`/export/${jobId}/status`);
    return res.data;
  } catch (e) {
    return handleError(e);
  }
}

export function getDownloadUrl(jobId: string): string {
  return `${API_BASE}/export/${jobId}/download`;
}

// ─── Streaming (SSE) helpers ─────────────────────────────────────────────────

/**
 * Connect to the export progress SSE stream.
 * Returns a function to close the connection.
 */
export function subscribeToExportProgress(
  jobId: string,
  onUpdate: (status: ExportStatus) => void,
  onError?: (err: Event) => void
): () => void {
  const es = new EventSource(`${API_BASE}/export/${jobId}/progress`);

  es.onmessage = (e) => {
    try {
      const data = JSON.parse(e.data) as ExportStatus;
      onUpdate(data);
      if (data.status === 'done' || data.status === 'error') {
        es.close();
      }
    } catch {
      // ignore parse errors
    }
  };

  if (onError) {
    es.onerror = onError;
  }

  return () => es.close();
}
