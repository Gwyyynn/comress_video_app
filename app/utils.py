"""Utility functions for file operations."""

import os
from pathlib import Path


def output_filename(path: str) -> str:
    """Generate a unique output filename to avoid overwriting existing files.
    
    If the target file exists, appends a numeric suffix until a unique name is found.
    For example: video.mp4 → video_1.mp4 → video_2.mp4, etc.
    
    Args:
        path: Target file path
        
    Returns:
        Unique file path (may be same as input if file doesn't exist)
    """
    if not os.path.exists(path):
        return path
        
    base, ext = os.path.splitext(path)
    counter = 1
    
    while True:
        new_path = f"{base}_{counter}{ext}"
        if not os.path.exists(new_path):
            return new_path
        counter += 1


def ensure_dir(dirpath: str) -> str:
    """Ensure directory exists, creating it if necessary.
    
    Args:
        dirpath: Directory path
        
    Returns:
        Absolute path to the directory
    """
    Path(dirpath).mkdir(parents=True, exist_ok=True)
    return os.path.abspath(dirpath)


def get_file_size_mb(filepath: str) -> float:
    """Get file size in megabytes.
    
    Args:
        filepath: Path to the file
        
    Returns:
        File size in MB
    """
    return os.path.getsize(filepath) / (1024 * 1024)
