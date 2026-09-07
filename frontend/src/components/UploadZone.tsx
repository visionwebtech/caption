/**
 * UploadZone — Drag-and-drop + click-to-upload component.
 * Works on both desktop and mobile.
 */

import { useRef, useState, useCallback } from 'react';
import { Upload, Film, AlertCircle } from 'lucide-react';
import { useAppStore } from '../store/captionStore';
import { uploadVideo, transcribeVideo } from '../lib/api';
import type { VideoInfo } from '../types';

const ALLOWED_TYPES = [
  'video/mp4',
  'video/quicktime',
  'video/x-msvideo',
  'video/webm',
  'video/x-matroska',
  'video/x-m4v',
];
const MAX_SIZE_MB = 500;

export function UploadZone() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const {
    setStage,
    setVideoInfo,
    setUploadProgress,
    setProcessingState,
    setTranscription,
    setSegments,
    setError,
  } = useAppStore();

  const validateFile = (file: File): string | null => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      return `Unsupported file type: ${file.type || 'unknown'}. Please upload MP4, MOV, AVI, WebM, or MKV.`;
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      return `File is too large (${(file.size / 1024 / 1024).toFixed(1)} MB). Maximum is ${MAX_SIZE_MB} MB.`;
    }
    return null;
  };

  const processFile = useCallback(async (file: File) => {
    setLocalError(null);
    const validationError = validateFile(file);
    if (validationError) {
      setLocalError(validationError);
      return;
    }

    // Create local URL for immediate preview
    const objectUrl = URL.createObjectURL(file);

    // ── 1. Upload ────────────────────────────────────────────────────────────
    setStage('uploading');
    setUploadProgress(0);

    let uploadResult;
    try {
      uploadResult = await uploadVideo(file, (progress) => {
        setUploadProgress(progress);
      });
    } catch (err) {
      setStage('upload');
      setLocalError(`Upload failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      URL.revokeObjectURL(objectUrl);
      return;
    }

    const videoInfo: VideoInfo = {
      jobId: uploadResult.job_id,
      filename: uploadResult.filename,
      sizeBytes: uploadResult.size_bytes,
      durationSeconds: uploadResult.duration_seconds,
      objectUrl,
    };
    setVideoInfo(videoInfo);

    // ── 2. Transcribe ─────────────────────────────────────────────────────────
    setStage('processing');
    setProcessingState('Extracting audio from video...', 10);

    try {
      setProcessingState('Transcribing speech with Whisper AI... (this may take 2-5 minutes for your first video)', 30);
      const result = await transcribeVideo(uploadResult.job_id);
      setTranscription(result);
      setSegments(result.segments);
      setStage('editor');
    } catch (err) {
      setStage('upload');
      setError(`Transcription failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
      URL.revokeObjectURL(objectUrl);
      return;
    }
  }, [setStage, setUploadProgress, setVideoInfo, setProcessingState, setTranscription, setSegments, setError]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) processFile(file);
    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) processFile(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = () => setIsDragOver(false);

  return (
    <div className="upload-page">
      <div className="upload-hero">
        <h1>CaptionFlow</h1>
        <p>
          Upload your video and let AI automatically generate captions in
          Hindi, English, or Hinglish — then style and export in minutes.
        </p>
      </div>

      <div
        className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => fileInputRef.current?.click()}
        role="button"
        tabIndex={0}
        onKeyDown={(e) => e.key === 'Enter' && fileInputRef.current?.click()}
        aria-label="Click or drag to upload a video"
      >
        <div className="upload-zone-icon">
          <Film size={32} />
        </div>
        <h3>Drop your video here</h3>
        <p>or tap to browse files</p>

        <div className="supported-formats">
          {['MP4', 'MOV', 'AVI', 'WebM', 'MKV'].map((f) => (
            <span key={f} className="format-badge">{f}</span>
          ))}
        </div>

        <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
          Max {MAX_SIZE_MB} MB · Optimized for 9:16 vertical video
        </p>

        <input
          ref={fileInputRef}
          type="file"
          accept="video/mp4,video/quicktime,video/x-msvideo,video/webm,video/x-matroska,video/x-m4v,.mp4,.mov,.avi,.webm,.mkv,.m4v"
          onChange={handleFileChange}
          style={{ display: 'none' }}
        />
      </div>

      {localError && (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '12px 16px',
            background: 'rgba(239,68,68,0.1)',
            border: '1px solid rgba(239,68,68,0.25)',
            borderRadius: 'var(--radius-md)',
            color: 'var(--color-error)',
            maxWidth: '520px',
            width: '100%',
          }}
        >
          <AlertCircle size={18} />
          <span style={{ fontSize: '0.875rem' }}>{localError}</span>
        </div>
      )}

      <div style={{ textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.8rem' }}>
        <Upload size={14} style={{ display: 'inline', marginRight: '4px' }} />
        Your video is processed locally. Nothing is sent to third-party servers.
      </div>
    </div>
  );
}
