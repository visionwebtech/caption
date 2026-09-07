/**
 * ProcessingScreen — Shown while audio extraction + transcription run.
 */

import { useAppStore } from '../store/captionStore';
import { Mic, Loader2 } from 'lucide-react';

export function ProcessingScreen() {
  const { processingMessage, processingProgress, videoInfo } = useAppStore();

  return (
    <div className="processing-screen">
      <div
        style={{
          width: 80,
          height: 80,
          background: 'linear-gradient(135deg, rgba(108,99,255,0.15), rgba(255,107,53,0.1))',
          borderRadius: 'var(--radius-xl)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'var(--color-brand-light)',
        }}
      >
        <Mic size={36} />
      </div>

      <div>
        <h2 style={{ marginBottom: '8px', fontSize: '1.4rem' }}>
          AI Transcription Running
        </h2>
        <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {videoInfo?.filename && (
            <span>
              Processing: <strong style={{ color: 'var(--text-secondary)' }}>{videoInfo.filename}</strong>
            </span>
          )}
        </p>
      </div>

      <div className="progress-container">
        <div className="progress-label">
          <span>{processingMessage || 'Initializing...'}</span>
          <span>{processingProgress}%</span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${processingProgress}%` }}
          />
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          color: 'var(--text-muted)',
          fontSize: '0.85rem',
        }}
      >
        <Loader2 size={16} style={{ animation: 'spin 1s linear infinite' }} />
        Using Whisper AI — no internet connection required
      </div>

      <div
        style={{
          background: 'var(--bg-elevated)',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '12px 20px',
          maxWidth: 480,
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
          lineHeight: '1.6',
        }}
      >
        <strong style={{ color: 'var(--text-secondary)' }}>⏱️ Estimated time:</strong> 2–5 minutes for a 1-minute video on CPU.
        The AI is working hard — please don't close this tab.
      </div>
    </div>
  );
}
