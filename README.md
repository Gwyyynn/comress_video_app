# Video Compressor (GUI)

A simple Python desktop app for downloading and compressing videos using **FFmpeg**.

## Features
- Download video from a link (via `yt-dlp`)
- Compress local video files
- Presets: **light / medium / strong**
- Optional **Target Size (MB)** mode using **2-pass encoding**
- GUI log output (no spammy popups)

---

## Requirements

### Python
Recommended: **Python 3.10+**

### FFmpeg (required)
The app runs FFmpeg through `subprocess`, so FFmpeg must be installed and available in `PATH`.

Check:
```bash
ffmpeg -version

Installation

Create and activate a virtual environment:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

Install dependencies:

pip install -r requirements.txt

Run the app:

python main.py



