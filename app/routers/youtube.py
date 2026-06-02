from fastapi import APIRouter, Depends, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.core.database import get_db
from app.schemas.schemas import DownloadRequest, VideoInfo, DownloadJobResponse
from app.services import youtube_service

router = APIRouter(prefix="/api/youtube", tags=["YouTube Downloader"])


@router.get("/info", response_model=VideoInfo)
def get_video_info(url: str, db: Session = Depends(get_db)):
    """
    Fetch metadata for a YouTube video without downloading it.
    Pass the YouTube URL as a query param: ?url=https://youtube.com/watch?v=...
    """
    return youtube_service.fetch_video_info(url)


@router.post("/download")
def download_video(payload: DownloadRequest, db: Session = Depends(get_db)):
    """
    Download a YouTube video or extract MP3 audio.
    Returns the file as a streaming download.
    """
    file_path, filename, media_type = youtube_service.download_video(db, payload)

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": "no-cache",
        },
    )


@router.get("/jobs", response_model=list[DownloadJobResponse])
def list_jobs(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    """List recent download jobs."""
    return youtube_service.list_jobs(db, skip=skip, limit=limit)
