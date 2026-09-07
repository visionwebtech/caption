/**
 * CaptionEditor — The editable transcript/timeline panel.
 * Lists all caption segments with edit, delete, split, merge controls.
 */

import { useState, useRef } from 'react';
import { Trash2, Scissors, Merge, ChevronDown, ChevronUp, Check, X } from 'lucide-react';
import { useAppStore } from '../store/captionStore';
import { updateCaptions, deleteSegment as apiDelete, splitSegment, mergeSegments } from '../lib/api';
import type { CaptionSegment } from '../types';

function formatTime(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  const ms = Math.round((seconds % 1) * 100);
  return `${m}:${s.toString().padStart(2, '0')}.${ms.toString().padStart(2, '0')}`;
}

interface SegmentCardProps {
  segment: CaptionSegment;
  isActive: boolean;
  isSelected: boolean;
  onActivate: () => void;
  onToggleSelect: () => void;
  onDelete: () => void;
  onSplit: () => void;
  onUpdate: (updates: Partial<CaptionSegment>) => void;
}

function SegmentCard({
  segment,
  isActive,
  isSelected,
  onActivate,
  onToggleSelect,
  onDelete,
  onSplit,
  onUpdate,
}: SegmentCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(segment.text);
  const [editStart, setEditStart] = useState(segment.start.toString());
  const [editEnd, setEditEnd] = useState(segment.end.toString());

  const saveEdit = () => {
    const newStart = parseFloat(editStart);
    const newEnd = parseFloat(editEnd);
    if (!isNaN(newStart) && !isNaN(newEnd) && newEnd > newStart && editText.trim()) {
      onUpdate({ text: editText.trim(), start: newStart, end: newEnd });
    }
    setIsEditing(false);
  };

  const cancelEdit = () => {
    setEditText(segment.text);
    setEditStart(segment.start.toString());
    setEditEnd(segment.end.toString());
    setIsEditing(false);
  };

  return (
    <div
      className={`caption-card ${isActive ? 'active' : ''}`}
      onClick={() => !isEditing && onActivate()}
    >
      {/* Top row: checkbox + time + actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
        <input
          type="checkbox"
          checked={isSelected}
          onChange={onToggleSelect}
          onClick={(e) => e.stopPropagation()}
          style={{ width: 16, height: 16, cursor: 'pointer', accentColor: 'var(--color-brand)' }}
          title="Select for merge"
        />

        {isEditing ? (
          <div style={{ display: 'flex', gap: '4px', flex: 1 }}>
            <input
              type="number"
              value={editStart}
              onChange={(e) => setEditStart(e.target.value)}
              step="0.1"
              style={{ width: '80px', fontSize: '0.75rem', padding: '4px 6px' }}
              title="Start time (seconds)"
            />
            <span style={{ color: 'var(--text-muted)', alignSelf: 'center' }}>→</span>
            <input
              type="number"
              value={editEnd}
              onChange={(e) => setEditEnd(e.target.value)}
              step="0.1"
              style={{ width: '80px', fontSize: '0.75rem', padding: '4px 6px' }}
              title="End time (seconds)"
            />
          </div>
        ) : (
          <div className="caption-card-time" style={{ flex: 1 }}>
            <span>{formatTime(segment.start)}</span>
            <span>→</span>
            <span>{formatTime(segment.end)}</span>
          </div>
        )}

        {/* Language badge */}
        {segment.language && (
          <span className={`lang-badge ${segment.language === 'hi' ? 'hi' : 'en'}`}>
            {segment.language.toUpperCase()}
          </span>
        )}
      </div>

      {/* Caption text */}
      {isEditing ? (
        <textarea
          value={editText}
          onChange={(e) => setEditText(e.target.value)}
          onClick={(e) => e.stopPropagation()}
          style={{ marginBottom: '8px', minHeight: '60px' }}
          autoFocus
        />
      ) : (
        <div
          className="caption-card-text"
          onDoubleClick={(e) => {
            e.stopPropagation();
            setIsEditing(true);
          }}
          title="Double-click to edit"
        >
          {segment.text}
        </div>
      )}

      {/* Actions */}
      <div className="caption-card-actions" style={{ opacity: 1 }}>
        {isEditing ? (
          <>
            <button
              className="btn btn-sm btn-primary"
              onClick={(e) => { e.stopPropagation(); saveEdit(); }}
            >
              <Check size={12} /> Save
            </button>
            <button
              className="btn btn-sm btn-secondary"
              onClick={(e) => { e.stopPropagation(); cancelEdit(); }}
            >
              <X size={12} /> Cancel
            </button>
          </>
        ) : (
          <>
            <button
              className="btn btn-sm btn-secondary"
              onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
              title="Edit this caption"
            >
              Edit
            </button>
            <button
              className="btn btn-sm btn-secondary"
              onClick={(e) => { e.stopPropagation(); onSplit(); }}
              title="Split at midpoint"
            >
              <Scissors size={12} /> Split
            </button>
            <button
              className="btn btn-sm btn-danger"
              onClick={(e) => { e.stopPropagation(); onDelete(); }}
              title="Delete this caption"
            >
              <Trash2 size={12} />
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export function CaptionEditor() {
  const {
    segments,
    setSegments,
    activeSegmentId,
    setActiveSegmentId,
    videoInfo,
    currentTime,
  } = useAppStore();

  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isBusy, setIsBusy] = useState(false);

  const jobId = videoInfo?.jobId;

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleDelete = async (id: string) => {
    if (!jobId || isBusy) return;
    setIsBusy(true);
    try {
      const updated = await apiDelete(jobId, id);
      setSegments(updated);
      if (activeSegmentId === id) setActiveSegmentId(null);
    } catch (e) {
      console.error('Delete failed:', e);
    } finally {
      setIsBusy(false);
    }
  };

  const handleSplit = async (id: string) => {
    if (!jobId || isBusy) return;
    const seg = segments.find((s) => s.id === id);
    if (!seg) return;
    const midpoint = (seg.start + seg.end) / 2;
    setIsBusy(true);
    try {
      const updated = await splitSegment(jobId, id, midpoint);
      setSegments(updated);
    } catch (e) {
      console.error('Split failed:', e);
    } finally {
      setIsBusy(false);
    }
  };

  const handleMerge = async () => {
    if (!jobId || isBusy || selectedIds.size < 2) return;
    setIsBusy(true);
    try {
      const updated = await mergeSegments(jobId, Array.from(selectedIds));
      setSegments(updated);
      setSelectedIds(new Set());
    } catch (e) {
      console.error('Merge failed:', e);
    } finally {
      setIsBusy(false);
    }
  };

  const handleUpdate = async (id: string, updates: Partial<CaptionSegment>) => {
    if (!jobId) return;
    const updated = segments.map((s) => (s.id === id ? { ...s, ...updates } : s));
    setSegments(updated);
    // Sync to backend in background
    updateCaptions(jobId, updated).catch(console.error);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <div className="panel-header">
        <h2>Captions ({segments.length})</h2>
        {selectedIds.size >= 2 && (
          <button
            className="btn btn-sm btn-primary"
            onClick={handleMerge}
            disabled={isBusy}
          >
            <Merge size={12} /> Merge {selectedIds.size}
          </button>
        )}
      </div>

      {/* Language info */}
      {segments.length > 0 && (
        <div style={{
          padding: '8px 12px',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          gap: '8px',
          alignItems: 'center',
          fontSize: '0.8rem',
          color: 'var(--text-muted)',
        }}>
          <span>Tip: Double-click text to edit. Check boxes to merge.</span>
        </div>
      )}

      {/* Segments list */}
      <div className="caption-list">
        {segments.length === 0 ? (
          <div style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '32px 16px', fontSize: '0.875rem' }}>
            No captions yet. Upload a video to get started.
          </div>
        ) : (
          segments.map((seg) => (
            <SegmentCard
              key={seg.id}
              segment={seg}
              isActive={activeSegmentId === seg.id || (currentTime >= seg.start && currentTime <= seg.end)}
              isSelected={selectedIds.has(seg.id)}
              onActivate={() => setActiveSegmentId(seg.id)}
              onToggleSelect={() => toggleSelect(seg.id)}
              onDelete={() => handleDelete(seg.id)}
              onSplit={() => handleSplit(seg.id)}
              onUpdate={(updates) => handleUpdate(seg.id, updates)}
            />
          ))
        )}
      </div>
    </div>
  );
}
