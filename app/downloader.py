"""Video downloader module using yt-dlp."""

import os
from typing import Optional
import yt_dlp


def download_video(url: str, out_dir: str = ".") -> str:
    """Download video from URL using yt-dlp.
    
    Supports YouTube, TikTok, and many other video hosting platforms.
    Downloads best quality video+audio and merges into MP4 format.
    
    Args:
        url: URL to the video
        out_dir: Output directory for downloaded video (default: current directory)
        
    Returns:
        Path to the downloaded video file
        
    Raises:
        yt_dlp.utils.DownloadError: If download fails
    """
    ydl_opts = {
        "outtmpl": os.path.join(out_dir, "%(title)s.%(ext)s"),
        "format": "bv*[vcodec^=avc1][ext=mp4]+ba[ext=m4a]/b[ext=mp4]",
        "merge_output_format": "mp4",
        "quiet": True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)
