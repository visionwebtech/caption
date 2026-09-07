/**
 * CaptionFlow — Global State Store (Zustand)
 * All app state lives here. Components read from and write to this store.
 * Think of it as the "brain" of the frontend.
 */

import { create } from 'zustand';
import type {
  AppStage,
  VideoInfo,
  CaptionSegment,
  CaptionStyle,
  ExportStatus,
  TranscriptionResult,
} from '../types';
import { DEFAULT_STYLE } from '../lib/captionPresets';

interface AppState {
  // ── App stage (what screen to show) ──────────────────────────────────────
  stage: AppStage;
  setStage: (stage: AppStage) => void;

  // ── Video info ────────────────────────────────────────────────────────────
  videoInfo: VideoInfo | null;
  setVideoInfo: (info: VideoInfo | null) => void;

  // ── Upload progress ───────────────────────────────────────────────────────
  uploadProgress: number;
  setUploadProgress: (p: number) => void;

  // ── Processing state ──────────────────────────────────────────────────────
  processingMessage: string;
  processingProgress: number;
  setProcessingState: (message: string, progress: number) => void;

  // ── Transcription result ──────────────────────────────────────────────────
  transcription: TranscriptionResult | null;
  setTranscription: (t: TranscriptionResult | null) => void;

  // ── Caption segments (editable by user) ──────────────────────────────────
  segments: CaptionSegment[];
  setSegments: (s: CaptionSegment[]) => void;
  updateSegment: (id: string, updates: Partial<CaptionSegment>) => void;
  deleteSegment: (id: string) => void;

  // ── Selected segment in editor ────────────────────────────────────────────
  activeSegmentId: string | null;
  setActiveSegmentId: (id: string | null) => void;

  // ── Caption style ─────────────────────────────────────────────────────────
  style: CaptionStyle;
  setStyle: (style: CaptionStyle) => void;
  updateStyleProp: <K extends keyof CaptionStyle>(key: K, value: CaptionStyle[K]) => void;

  // ── Current video time (from player) ─────────────────────────────────────
  currentTime: number;
  setCurrentTime: (t: number) => void;

  // ── Export state ──────────────────────────────────────────────────────────
  exportStatus: ExportStatus | null;
  setExportStatus: (s: ExportStatus | null) => void;

  // ── Error ─────────────────────────────────────────────────────────────────
  error: string | null;
  setError: (e: string | null) => void;

  // ── Reset (start over) ────────────────────────────────────────────────────
  reset: () => void;
}

const initialState = {
  stage: 'upload' as AppStage,
  videoInfo: null,
  uploadProgress: 0,
  processingMessage: '',
  processingProgress: 0,
  transcription: null,
  segments: [],
  activeSegmentId: null,
  style: DEFAULT_STYLE,
  currentTime: 0,
  exportStatus: null,
  error: null,
};

export const useAppStore = create<AppState>((set) => ({
  ...initialState,

  setStage: (stage) => set({ stage }),
  setVideoInfo: (videoInfo) => set({ videoInfo }),
  setUploadProgress: (uploadProgress) => set({ uploadProgress }),

  setProcessingState: (processingMessage, processingProgress) =>
    set({ processingMessage, processingProgress }),

  setTranscription: (transcription) => set({ transcription }),

  setSegments: (segments) => set({ segments }),

  updateSegment: (id, updates) =>
    set((state) => ({
      segments: state.segments.map((s) =>
        s.id === id ? { ...s, ...updates } : s
      ),
    })),

  deleteSegment: (id) =>
    set((state) => ({
      segments: state.segments.filter((s) => s.id !== id),
    })),

  setActiveSegmentId: (activeSegmentId) => set({ activeSegmentId }),

  setStyle: (style) => set({ style }),

  updateStyleProp: (key, value) =>
    set((state) => ({
      style: { ...state.style, [key]: value },
    })),

  setCurrentTime: (currentTime) => set({ currentTime }),
  setExportStatus: (exportStatus) => set({ exportStatus }),
  setError: (error) => set({ error }),

  reset: () => {
    // Release the blob URL to free memory
    set((state) => {
      if (state.videoInfo?.objectUrl) {
        URL.revokeObjectURL(state.videoInfo.objectUrl);
      }
      return { ...initialState };
    });
  },
}));

// ─── Selectors ────────────────────────────────────────────────────────────────

/** Returns the caption segment that should be visible at the current time. */
export function useCurrentCaption(): CaptionSegment | null {
  return useAppStore((state) => {
    const { currentTime, segments } = state;
    return (
      segments.find(
        (s) => currentTime >= s.start && currentTime <= s.end
      ) ?? null
    );
  });
}
