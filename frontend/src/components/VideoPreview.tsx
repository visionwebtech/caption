/**
 * VideoPreview — Video player with real-time caption overlay.
 * Shows the video + captions rendered live on a canvas.
 */

import { useRef, useEffect, useState, useCallback } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';
import { useAppStore } from '../store/captionStore';
import { CaptionOverlay } from './CaptionOverlay';

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

export function VideoPreview() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [duration, setDuration] = useState(0);
  const [videoDims, setVideoDims] = useState({ width: 0, height: 0 });

  const { videoInfo, currentTime, setCurrentTime } = useAppStore();

  // Sync video time to store
  const handleTimeUpdate = useCallback(() => {
    if (videoRef.current) {
      setCurrentTime(videoRef.current.currentTime);
    }
  }, [setCurrentTime]);

  const handleLoadedMetadata = () => {
    if (videoRef.current) {
      setDuration(videoRef.current.duration);
    }
  };

  const handleVideoSize = () => {
    if (videoRef.current) {
      setVideoDims({
        width: videoRef.current.clientWidth,
        height: videoRef.current.clientHeight,
      });
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
    video.addEventListener('timeupdate', handleTimeUpdate);
    video.addEventListener('loadedmetadata', handleLoadedMetadata);
    video.addEventListener('loadeddata', handleVideoSize);
    window.addEventListener('resize', handleVideoSize);
    return () => {
      video.removeEventListener('timeupdate', handleTimeUpdate);
      video.removeEventListener('loadedmetadata', handleLoadedMetadata);
      video.removeEventListener('loadeddata', handleVideoSize);
      window.removeEventListener('resize', handleVideoSize);
    };
  }, [handleTimeUpdate]);

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (isPlaying) {
      video.pause();
      setIsPlaying(false);
    } else {
      video.play().then(() => setIsPlaying(true)).catch(() => {});
    }
  };

  const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
    const t = Number(e.target.value);
    if (videoRef.current) {
      videoRef.current.currentTime = t;
      setCurrentTime(t);
    }
  };

  const handleRestart = () => {
    if (videoRef.current) {
      videoRef.current.currentTime = 0;
      setCurrentTime(0);
    }
  };

  if (!videoInfo) return null;

  return (
    <div className="preview-container">
      <div className="video-wrapper" ref={wrapperRef}>
        <video
          ref={videoRef}
          src={videoInfo.objectUrl}
          playsInline
          preload="metadata"
          onEnded={() => setIsPlaying(false)}
          style={{ maxHeight: '60vh', maxWidth: '100%', display: 'block' }}
        />
        {/* Canvas overlay for captions */}
        {videoDims.width > 0 && (
          <CaptionOverlay
            width={videoDims.width}
            height={videoDims.height}
          />
        )}
      </div>

      {/* Player Controls */}
      <div style={{ width: '100%', maxWidth: '600px', padding: '0 16px' }}>
        {/* Seek bar */}
        <input
          type="range"
          min={0}
          max={duration || 0}
          step={0.1}
          value={currentTime}
          onChange={handleSeek}
          style={{ width: '100%', marginBottom: '8px' }}
          aria-label="Video seek bar"
        />

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', fontFamily: 'monospace' }}>
            {formatTime(currentTime)} / {formatTime(duration)}
          </span>

          <div className="preview-controls">
            <button
              className="btn btn-ghost btn-icon"
              onClick={handleRestart}
              title="Restart"
              aria-label="Restart video"
            >
              <RotateCcw size={16} />
            </button>

            <button
              className="btn btn-primary btn-icon"
              onClick={togglePlay}
              aria-label={isPlaying ? 'Pause' : 'Play'}
            >
              {isPlaying ? <Pause size={18} /> : <Play size={18} />}
            </button>
          </div>

          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
            {videoInfo.filename}
          </span>
        </div>
      </div>
    </div>
  );
}
