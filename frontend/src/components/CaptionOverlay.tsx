/**
 * CaptionOverlay — Renders captions on top of the video preview.
 * Uses Canvas 2D for real-time rendering with full style support.
 * Updates whenever style, segments, or currentTime changes.
 */

import { useEffect, useRef } from 'react';
import { useAppStore, useCurrentCaption } from '../store/captionStore';
import { getFontStack, detectFontForText } from '../lib/fonts';

interface Props {
  width: number;
  height: number;
}

export function CaptionOverlay({ width, height }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { style, currentTime } = useAppStore();
  const activeCaption = useCurrentCaption();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    if (!activeCaption?.text) return;

    const text = activeCaption.text;
    const lang = activeCaption.language ?? 'en';

    // Auto-detect font for the text content (important for Hindi)
    const fontFamily = detectFontForText(text, style.font_family);
    const fontStack = getFontStack(fontFamily);
    const fontSize = Math.round((style.font_size / 1080) * height); // scale to canvas
    const lineHeight = fontSize * style.line_spacing;

    // Set font
    ctx.font = `${style.font_weight} ${fontSize}px ${fontStack}`;
    ctx.textAlign = style.horizontal_alignment as CanvasTextAlign;
    ctx.textBaseline = 'bottom';

    // Word wrap
    const maxWidth = width * 0.9;
    const lines = wrapText(ctx, text, maxWidth);

    // Calculate total height
    const totalHeight = lines.length * lineHeight;

    // Position
    const yBase = height * style.vertical_position;
    const xBase =
      style.horizontal_alignment === 'left'
        ? width * 0.05
        : style.horizontal_alignment === 'right'
        ? width * 0.95
        : width / 2;

    // Draw each line
    lines.forEach((line, i) => {
      const y = yBase - totalHeight + (i + 1) * lineHeight;

      // Background box
      if (style.background_enabled) {
        const metrics = ctx.measureText(line);
        const boxW = metrics.width + style.background_padding * 2;
        const boxH = lineHeight + style.background_padding;
        const boxX =
          style.horizontal_alignment === 'center'
            ? xBase - boxW / 2
            : style.horizontal_alignment === 'right'
            ? xBase - boxW
            : xBase - style.background_padding;
        const boxY = y - lineHeight - style.background_padding / 2;

        ctx.save();
        ctx.globalAlpha = style.background_opacity;
        ctx.fillStyle = style.background_color;
        if (style.border_radius > 0) {
          roundRect(ctx, boxX, boxY, boxW, boxH, style.border_radius);
          ctx.fill();
        } else {
          ctx.fillRect(boxX, boxY, boxW, boxH);
        }
        ctx.restore();
      }

      // Shadow
      if (style.shadow_enabled) {
        ctx.shadowColor = style.shadow_color;
        ctx.shadowBlur = style.shadow_intensity * 20;
        ctx.shadowOffsetX = style.shadow_offset_x;
        ctx.shadowOffsetY = style.shadow_offset_y;
      } else {
        ctx.shadowColor = 'transparent';
        ctx.shadowBlur = 0;
        ctx.shadowOffsetX = 0;
        ctx.shadowOffsetY = 0;
      }

      // Outline/stroke
      if (style.outline_enabled && style.outline_thickness > 0) {
        ctx.strokeStyle = style.outline_color;
        ctx.lineWidth = style.outline_thickness * 2;
        ctx.lineJoin = 'round';
        ctx.strokeText(line, xBase, y);
      }

      // Main text
      ctx.fillStyle = style.text_color;
      ctx.fillText(line, xBase, y);
    });
  }, [activeCaption, style, currentTime, width, height]);

  return (
    <canvas
      ref={canvasRef}
      width={width}
      height={height}
      style={{
        position: 'absolute',
        inset: 0,
        pointerEvents: 'none',
        borderRadius: 'inherit',
      }}
    />
  );
}

// ─── Helpers ─────────────────────────────────────────────────────────────────

function wrapText(ctx: CanvasRenderingContext2D, text: string, maxWidth: number): string[] {
  const words = text.split(' ');
  const lines: string[] = [];
  let current = '';

  for (const word of words) {
    const test = current ? `${current} ${word}` : word;
    if (ctx.measureText(test).width > maxWidth && current) {
      lines.push(current);
      current = word;
    } else {
      current = test;
    }
  }
  if (current) lines.push(current);
  return lines;
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  r: number
) {
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
}
