"""
CaptionFlow — Video Render Service
Burns captions permanently into the video using FFmpeg drawtext filters.
Supports all caption styles from the frontend.
"""

import asyncio
import shutil
import os
from typing import List, Callable, Optional
from pathlib import Path
from models.caption import CaptionSegment, CaptionStyle, TextAlignment
from utils.sanitize import sanitize_for_ffmpeg


def _check_ffmpeg():
    if not shutil.which("ffmpeg"):
        raise FileNotFoundError(
            "FFmpeg not found. Please install FFmpeg:\n"
            "  Windows: winget install Gyan.FFmpeg\n"
            "  Then restart your terminal."
        )


def _hex_to_ffmpeg_color(hex_color: str, opacity: float = 1.0) -> str:
    """
    Convert a hex color (#RRGGBB) to FFmpeg color format (0xAARRGGBB).
    Opacity is 0.0 (transparent) to 1.0 (opaque).
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    a = int(opacity * 255)
    
    # FFmpeg uses 0xAARRGGBB format
    return f"0x{a:02X}{r:02X}{g:02X}{b:02X}"


def _get_font_path(font_family: str, language: str = "en") -> str:
    """
    Map a font family name to a system font file path.
    For Hindi (Devanagari), always use a compatible font.
    Falls back to a safe default if the font isn't found.
    """
    # Devanagari languages always need Noto Sans Devanagari
    devanagari_langs = {"hi", "mr", "ne", "sa", "mai", "bho", "awa", "raj"}
    if language in devanagari_langs:
        font_family = "Noto Sans Devanagari"

    # Font search paths on Windows
    font_dirs = [
        r"C:\Windows\Fonts",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Windows\Fonts"),
    ]

    font_map = {
        "Poppins": ["Poppins-Bold.ttf", "Poppins-SemiBold.ttf", "Poppins-Regular.ttf"],
        "Montserrat": ["Montserrat-Bold.ttf", "Montserrat-SemiBold.ttf", "Montserrat-Regular.ttf"],
        "Inter": ["Inter-Bold.ttf", "Inter-SemiBold.ttf", "Inter-Regular.ttf"],
        "Noto Sans": ["NotoSans-Bold.ttf", "NotoSans-Regular.ttf"],
        "Noto Sans Devanagari": [
            "NotoSansDevanagari-Bold.ttf",
            "NotoSansDevanagari-SemiBold.ttf",
            "NotoSansDevanagari-Regular.ttf",
        ],
        "Arial": ["arialbd.ttf", "arial.ttf"],
        "Roboto": ["Roboto-Bold.ttf", "Roboto-Regular.ttf"],
    }

    candidates = font_map.get(font_family, []) + ["arialbd.ttf", "arial.ttf"]
    
    for font_dir in font_dirs:
        for font_file in candidates:
            path = os.path.join(font_dir, font_file)
            if os.path.exists(path):
                return path

    # Ultimate fallback
    return r"C:\Windows\Fonts\arial.ttf"


def _build_drawtext_filters(
    segments: List[CaptionSegment],
    style: CaptionStyle,
    video_width: int = 1080,
    video_height: int = 1920,
) -> str:
    """
    Build FFmpeg drawtext filter chains for all caption segments.
    Each segment becomes a timed drawtext filter.
    """
    if not segments:
        return ""

    filters = []
    
    # Determine language for font selection
    lang = segments[0].language or "en"
    font_path = _get_font_path(style.font_family, lang)
    # Escape backslashes for FFmpeg filter syntax
    font_path_escaped = font_path.replace("\\", "/").replace(":", "\\:")

    # Calculate vertical position in pixels
    y_pos = int(style.vertical_position * video_height)

    # Text color
    text_color = style.text_color.lstrip("#")
    font_color_hex = f"0xFF{text_color[0:2]}{text_color[2:4]}{text_color[4:6]}" if len(text_color) == 6 else "0xFFFFFFFF"

    for seg in segments:
        text = sanitize_for_ffmpeg(seg.text)
        if not text:
            continue

        start = seg.start
        end = seg.end

        # Build drawtext for this segment
        dt_parts = [
            f"fontfile='{font_path_escaped}'",
            f"text='{text}'",
            f"fontsize={style.font_size}",
            f"fontcolor={font_color_hex}",
            f"x=(w-text_w)/2",  # horizontally centered (default)
            f"y={y_pos}-text_h",
            f"enable='between(t,{start:.3f},{end:.3f})'",
            "line_spacing=5",
        ]

        # Horizontal alignment adjustment
        if style.horizontal_alignment == TextAlignment.left:
            dt_parts[3] = "x=20"  # left margin
        elif style.horizontal_alignment == TextAlignment.right:
            dt_parts[3] = "x=w-text_w-20"  # right margin

        # Outline / border
        if style.outline_enabled and style.outline_thickness > 0:
            outline_color = style.outline_color.lstrip("#")
            outline_hex = f"0xFF{outline_color}" if len(outline_color) == 6 else "0xFF000000"
            dt_parts.append(f"borderw={style.outline_thickness}")
            dt_parts.append(f"bordercolor={outline_hex}")

        # Shadow
        if style.shadow_enabled:
            shadow_color = style.shadow_color.lstrip("#")
            shadow_alpha = int(style.shadow_intensity * 255)
            shadow_hex = f"0x{shadow_alpha:02X}{shadow_color}" if len(shadow_color) == 6 else "0x80000000"
            dt_parts.append(f"shadowx={style.shadow_offset_x}")
            dt_parts.append(f"shadowy={style.shadow_offset_y}")
            dt_parts.append(f"shadowcolor={shadow_hex}")

        # Background box
        if style.background_enabled:
            bg_color = style.background_color.lstrip("#")
            bg_alpha = int(style.background_opacity * 255)
            bg_hex = f"0x{bg_alpha:02X}{bg_color}" if len(bg_color) == 6 else "0x99000000"
            dt_parts.append("box=1")
            dt_parts.append(f"boxcolor={bg_hex}")
            dt_parts.append(f"boxborderw={style.background_padding}")

        filters.append(f"drawtext={':'.join(dt_parts)}")

    return ",".join(filters)


async def render_video(
    job_id: str,
    input_video: str,
    output_path: str,
    segments: List[CaptionSegment],
    style: CaptionStyle,
    progress_callback: Optional[Callable] = None,
) -> None:
    """
    Render captions burned into the video using FFmpeg.
    
    Args:
        job_id: Job identifier
        input_video: Path to input video file
        output_path: Where to write the output MP4
        segments: Caption segments with timing and text
        style: Visual styling for captions
        progress_callback: Called with (progress%, message) during render
    """
    _check_ffmpeg()

    if not segments:
        raise ValueError("No caption segments provided for rendering.")

    if progress_callback:
        progress_callback(15.0, "Preparing caption filters...")

    # Build the drawtext filter chain
    vf_filter = _build_drawtext_filters(segments, style)

    if not vf_filter:
        raise ValueError("Failed to generate caption filters.")

    if progress_callback:
        progress_callback(30.0, "Starting FFmpeg render...")

    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        "ffmpeg",
        "-i", str(input_video),
        "-vf", vf_filter,
        "-c:v", "libx264",     # H.264 video codec (universal compatibility)
        "-preset", "fast",      # Encoding speed (fast = good quality + reasonable speed)
        "-crf", "23",           # Quality (18=high, 28=low; 23 is default)
        "-c:a", "aac",          # AAC audio codec
        "-b:a", "128k",         # Audio bitrate
        "-movflags", "+faststart",  # Optimize for web streaming
        "-y",                   # Overwrite output
        str(output_path),
    ]

    if progress_callback:
        progress_callback(40.0, "Rendering video... (this may take several minutes)")

    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Stream FFmpeg stderr to parse progress
        progress_lines = []
        while True:
            line = await proc.stderr.readline()
            if not line:
                break
            decoded = line.decode("utf-8", errors="replace").strip()
            progress_lines.append(decoded)

            # Parse FFmpeg progress from "time=HH:MM:SS.ms" in stderr
            if "time=" in decoded and progress_callback:
                time_str = decoded.split("time=")[1].split()[0]
                try:
                    h, m, s = time_str.split(":")
                    current_seconds = int(h) * 3600 + int(m) * 60 + float(s)
                    # Estimate total from last segment end
                    total = segments[-1].end if segments else 60.0
                    render_progress = min(95.0, 40.0 + (current_seconds / total) * 55.0)
                    progress_callback(render_progress, f"Rendering... {time_str}")
                except Exception:
                    pass

        await proc.wait()

        if proc.returncode != 0:
            error_output = "\n".join(progress_lines[-20:])  # Last 20 lines
            raise RuntimeError(
                f"FFmpeg render failed (exit {proc.returncode}):\n{error_output}"
            )

        if not Path(output_path).exists():
            raise RuntimeError("FFmpeg completed but output file was not created.")

        if progress_callback:
            progress_callback(99.0, "Finalizing video...")

    except FileNotFoundError:
        raise
    except RuntimeError:
        raise
    except Exception as e:
        raise RuntimeError(f"Unexpected render error: {str(e)}")
