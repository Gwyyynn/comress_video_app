"""Video compression module using FFmpeg.

Supports two encoding modes:
- CRF (Constant Rate Factor): Quality-based compression
- 2-Pass: Target size-based compression with precise bitrate control
"""

import os
import shutil
import subprocess
from typing import Optional, Tuple
import ffmpeg

from app.presets import get_preset, PresetConfig
from app.utils import get_file_size_mb


def get_video_info(path: str) -> Tuple[int, int, float, int, float]:
    """Extract video metadata from file.
    
    Args:
        path: Path to video file
        
    Returns:
        Tuple of (width, height, duration_seconds, bitrate_kbps)
        
    Raises:
        ffmpeg.Error: If probe fails or stream not found
    """
    probe = ffmpeg.probe(path)
    video_stream = next(
        (s for s in probe["streams"] if s["codec_type"] == "video"),
        None
    )
    
    if not video_stream:
        raise ValueError(f"No video stream found in {path}")
    
    width = int(video_stream["width"])
    height = int(video_stream["height"])
    duration = float(probe["format"]["duration"])
    bitrate = int(probe["format"].get("bit_rate", 0)) // 1000  # kbps
    
    size_mb = get_file_size_mb(path)
    return width, height, duration, bitrate, size_mb


def compress_video(
    input_file: str,
    output_file: str,
    preset: str = "medium",
    target_mb: Optional[int] = None
) -> float:
    """Compress video with specified preset and optional target size.
    
    Two compression modes:
    1. Target MB mode: Uses 2-pass encoding to meet exact size requirement
    2. CRF mode (default): Uses constant quality factor with optional scaling
    
    Args:
        input_file: Path to input video
        output_file: Path for output compressed video
        preset: Compression preset ('light', 'medium', or 'strong')
        target_mb: Optional target file size in MB; if provided uses 2-pass encoding
        
    Returns:
        Compressed file size in MB
        
    Raises:
        KeyError: If preset is invalid
        ValueError: If video probe fails
    """
    # Get preset configuration
    preset_config = get_preset(preset)
    
    # Extract video info
    width, height, duration, src_kbps, src_size_mb = get_video_info(input_file)
    
    # Calculate scaling filter
    max_height = preset_config["max_height"]
    scale_filter = f"scale=-2:{max_height}"
    
    audio_kbps = 96
    
    if target_mb is not None:
        if src_size_mb <= (target_mb - 0.2):
            shutil.copy(input_file, output_file)
            return get_file_size_mb(output_file)

    # ========= TARGET MB MODE (2-PASS ENCODING) =========
    if target_mb:
        # Calculate video bitrate to meet target size
        total_kbps = int(target_mb * 8192 / duration)
        video_kbps = max(total_kbps - audio_kbps, 300)
        
        _two_pass_encode(
            input_file,
            output_file,
            scale_filter,
            video_kbps,
            audio_kbps,
            preset_config["preset"]
        )
        
        # Clean up ffmpeg log files
        for logfile in ("ffmpeg2pass-0.log", "ffmpeg2pass-0.log.mbtree"):
            if os.path.exists(logfile):
                os.remove(logfile)
        
        return get_file_size_mb(output_file)
    
    # ========= NORMAL MODE (CRF - CONSTANT RATE FACTOR) =========
    # Calculate video bitrate based on preset
    video_kbps = max(
        int(src_kbps * preset_config["video_kbps_mult"]), 
        350
    ) if src_kbps else 1200
    
    # Skip encoding if source is already smaller than target
    if src_kbps and src_kbps <= video_kbps:
        shutil.copy(input_file, output_file)
        return get_file_size_mb(output_file)
    
    # Single-pass encoding
    _one_pass_encode(
        input_file,
        output_file,
        scale_filter,
        video_kbps,
        audio_kbps,
        preset_config["preset"]
    )
    
    return get_file_size_mb(output_file)


def _two_pass_encode(
    input_file: str,
    output_file: str,
    scale_filter: str,
    video_kbps: int,
    audio_kbps: int,
    preset: str
) -> None:
    """Encode video using 2-pass encoding for precise bitrate control.
    
    First pass analyzes content, second pass encodes with calculated bitrate.
    
    Args:
        input_file: Path to input video
        output_file: Path for output video
        scale_filter: FFmpeg scale filter string
        video_kbps: Target video bitrate in kbps
        audio_kbps: Audio bitrate in kbps
        preset: FFmpeg preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    """
    null_device = "NUL" if os.name == "nt" else "/dev/null"
    
    # PASS 1: Analysis pass
    cmd_pass1 = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-b:v", f"{video_kbps}k",
        "-pass", "1",
        "-preset", preset,
        "-an",
        "-f", "mp4",
        null_device
    ]
    
    # PASS 2: Encoding pass
    cmd_pass2 = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-b:v", f"{video_kbps}k",
        "-pass", "2",
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", f"{audio_kbps}k",
        "-movflags", "+faststart",
        output_file
    ]
    
    subprocess.run(
        cmd_pass1,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
    subprocess.run(
        cmd_pass2,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )


def _one_pass_encode(
    input_file: str,
    output_file: str,
    scale_filter: str,
    video_kbps: int,
    audio_kbps: int,
    preset: str
) -> None:
    """Encode video using single-pass encoding.
    
    Args:
        input_file: Path to input video
        output_file: Path for output video
        scale_filter: FFmpeg scale filter string
        video_kbps: Target video bitrate in kbps
        audio_kbps: Audio bitrate in kbps
        preset: FFmpeg preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", input_file,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-b:v", f"{video_kbps}k",
        "-preset", preset,
        "-c:a", "aac",
        "-b:a", f"{audio_kbps}k",
        "-movflags", "+faststart",
        output_file
    ]
    
    subprocess.run(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=True
    )
