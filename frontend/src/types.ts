/**
 * CaptionFlow — TypeScript Types
 * Shared types used across all frontend components.
 */

// ─── Caption Types ──────────────────────────────────────────────────────────

export interface WordTimestamp {
  word: string;
  start: number;
  end: number;
  probability?: number;
}

export interface CaptionSegment {
  id: string;
  start: number;
  end: number;
  text: string;
  language?: string;
  words?: WordTimestamp[];
}

// ─── Style Types ─────────────────────────────────────────────────────────────

export type TextAlignment = 'left' | 'center' | 'right';

export type AnimationType =
  | 'none'
  | 'fade'
  | 'pop'
  | 'scale'
  | 'slide_up'
  | 'slide_down'
  | 'word_pop'
  | 'word_highlight'
  | 'type_reveal';

export interface CaptionStyle {
  preset_name?: string;
  // Font
  font_family: string;
  font_size: number;
  font_weight: string;
  // Colors
  text_color: string;
  highlight_color: string;
  // Background
  background_enabled: boolean;
  background_color: string;
  background_opacity: number;
  background_padding: number;
  border_radius: number;
  // Outline
  outline_enabled: boolean;
  outline_color: string;
  outline_thickness: number;
  // Shadow
  shadow_enabled: boolean;
  shadow_color: string;
  shadow_intensity: number;
  shadow_offset_x: number;
  shadow_offset_y: number;
  // Position
  vertical_position: number;
  horizontal_alignment: TextAlignment;
  max_chars_per_line: number;
  // Typography
  line_spacing: number;
  letter_spacing: number;
  // Animation
  animation: AnimationType;
  word_highlight_enabled: boolean;
  word_highlight_color: string;
}

// ─── App State Types ─────────────────────────────────────────────────────────

export type AppStage =
  | 'upload'        // Initial state: show upload zone
  | 'uploading'     // File is being uploaded
  | 'processing'    // Audio extraction + transcription running
  | 'editor'        // Main editor open
  | 'exporting'     // FFmpeg render running
  | 'done';         // Render complete, download available

export interface VideoInfo {
  jobId: string;
  filename: string;
  sizeBytes: number;
  durationSeconds?: number;
  objectUrl: string; // Local blob URL for preview
}

export interface TranscriptionResult {
  jobId: string;
  language: string;
  languageProbability: number;
  segments: CaptionSegment[];
  durationSeconds: number;
  modelUsed: string;
}

export interface ExportStatus {
  jobId: string;
  status: 'queued' | 'processing' | 'done' | 'error';
  progress: number;
  message: string;
  downloadUrl?: string;
  fileSizeBytes?: number;
}

// ─── API Response Types ───────────────────────────────────────────────────────

export interface UploadResponse {
  job_id: string;
  filename: string;
  size_bytes: number;
  duration_seconds?: number;
  message: string;
}

export interface ApiError {
  error: string;
  detail?: string;
  code?: string;
}
