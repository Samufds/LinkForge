import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import yt_dlp
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.models import DownloadJob
from app.schemas.schemas import DownloadRequest, VideoInfo


# ─────────────────────────────────────────────
#  yt-dlp helpers
# ─────────────────────────────────────────────

def _common_opts() -> dict:
    """Shared yt-dlp options that mimic a real browser and avoid 403s."""
    return {
        "quiet": True,
        "no_warnings": True,
        # Use cookies from your local Chrome/Firefox — this is the key fix
        "cookiesfrombrowser": ("chrome",),   # change to "firefox" if you use Firefox
        # Spoof a real browser User-Agent
        "http_headers": {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        },
        # Retry on transient failures
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        # Use the android client as fallback — bypasses some restrictions
        "extractor_args": {
            "youtube": {
                "player_client": ["android", "web"],
            }
        },
    }


def _ydl_opts_info() -> dict:
    """Options for fetching video metadata only (no download)."""
    return {
        **_common_opts(),
        "skip_download": True,
        "extract_flat": False,
    }


def _quality_to_format(format: str, quality: str) -> str:
    """Map our quality string to a yt-dlp format selector."""
    if format == "mp3":
        return "bestaudio/best"
    quality_map = {
        "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
        "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720][ext=mp4]/best",
        "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480][ext=mp4]/best",
        "360p": "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360][ext=mp4]/best",
    }
    return quality_map.get(quality, quality_map["best"])


# ─────────────────────────────────────────────
#  Public service functions
# ─────────────────────────────────────────────

def fetch_video_info(video_url: str) -> VideoInfo:
    """Fetch metadata about a YouTube video without downloading it."""
    try:
        with yt_dlp.YoutubeDL(_ydl_opts_info()) as ydl:
            info = ydl.extract_info(video_url, download=False)
    except yt_dlp.utils.DownloadError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Could not fetch video info: {str(e)}",
        )

    # Collect available formats for the frontend to display
    formats = []
    for f in (info.get("formats") or []):
        if f.get("vcodec") != "none" and f.get("ext") in ("mp4", "webm"):
            formats.append({
                "format_id": f.get("format_id"),
                "ext": f.get("ext"),
                "height": f.get("height"),
                "fps": f.get("fps"),
                "filesize": f.get("filesize"),
            })
    # Deduplicate by height
    seen = set()
    unique_formats = []
    for f in sorted(formats, key=lambda x: x.get("height") or 0, reverse=True):
        h = f.get("height")
        if h not in seen:
            seen.add(h)
            unique_formats.append(f)

    return VideoInfo(
        title=info.get("title", "Unknown"),
        duration=info.get("duration"),
        thumbnail=info.get("thumbnail"),
        uploader=info.get("uploader"),
        view_count=info.get("view_count"),
        formats=unique_formats[:8],  # Top 8 formats
    )


def download_video(db: Session, payload: DownloadRequest) -> tuple[Path, str, str]:
    """
    Download a YouTube video to a temp file.
    Returns (file_path, filename, media_type).
    Also persists a DownloadJob record.
    """

    # Persist job record
    job = DownloadJob(
        video_url=payload.video_url,
        format=payload.format,
        quality=payload.quality,
        status="processing",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    try:
        tmpdir = tempfile.mkdtemp()
        fmt_selector = _quality_to_format(payload.format, payload.quality)

        ydl_opts = {
            **_common_opts(),
            "format": fmt_selector,
            "outtmpl": os.path.join(tmpdir, "%(title)s.%(ext)s"),
        }

        if payload.format == "mp3":
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(payload.video_url, download=True)
            title = info.get("title", "video")
            video_id = info.get("id", "")

        # Find the downloaded file
        files = list(Path(tmpdir).iterdir())
        if not files:
            raise RuntimeError("yt-dlp completed but no file was found.")
        downloaded_file = files[0]

        # Update DB record
        safe_title = re.sub(r'[^\w\s-]', '', title)[:100]
        job.status = "done"
        job.video_title = title
        job.video_id = video_id
        db.commit()

        media_type = "audio/mpeg" if payload.format == "mp3" else "video/mp4"
        filename = f"{safe_title}.{payload.format}"
        return downloaded_file, filename, media_type

    except Exception as e:
        job.status = "failed"
        job.error_message = str(e)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}",
        )


def list_jobs(db: Session, skip: int = 0, limit: int = 20) -> list[DownloadJob]:
    return db.query(DownloadJob).order_by(DownloadJob.created_at.desc()).offset(skip).limit(limit).all()
