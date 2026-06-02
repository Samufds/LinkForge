from pydantic import BaseModel, HttpUrl, field_validator, model_validator
from typing import Optional
from datetime import datetime
import re


# ─────────────────────────────────────────────
#  URL Shortener Schemas
# ─────────────────────────────────────────────

class URLCreate(BaseModel):
    original_url: HttpUrl
    custom_alias: Optional[str] = None

    @field_validator("custom_alias")
    @classmethod
    def validate_alias(cls, v):
        if v is None:
            return v
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Alias must be at least 3 characters.")
        if len(v) > 50:
            raise ValueError("Alias must be 50 characters or fewer.")
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError("Alias can only contain letters, numbers, hyphens, and underscores.")
        return v


class URLResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    custom_alias: Optional[str]
    short_url: str          # Computed field — full shortened URL
    click_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class URLStats(BaseModel):
    short_code: str
    original_url: str
    click_count: int
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ─────────────────────────────────────────────
#  YouTube Downloader Schemas
# ─────────────────────────────────────────────

YOUTUBE_PATTERN = re.compile(
    r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+'
)


class DownloadRequest(BaseModel):
    video_url: str
    format: str = "mp4"
    quality: str = "best"

    @field_validator("video_url")
    @classmethod
    def validate_youtube_url(cls, v):
        v = v.strip()
        if not YOUTUBE_PATTERN.match(v):
            raise ValueError("URL must be a valid YouTube link.")
        return v

    @field_validator("format")
    @classmethod
    def validate_format(cls, v):
        if v not in ("mp4", "mp3"):
            raise ValueError("Format must be 'mp4' or 'mp3'.")
        return v

    @field_validator("quality")
    @classmethod
    def validate_quality(cls, v):
        allowed = {"best", "720p", "480p", "360p"}
        if v not in allowed:
            raise ValueError(f"Quality must be one of: {', '.join(allowed)}")
        return v


class VideoInfo(BaseModel):
    title: str
    duration: Optional[int]       # seconds
    thumbnail: Optional[str]
    uploader: Optional[str]
    view_count: Optional[int]
    formats: list[dict]


class DownloadJobResponse(BaseModel):
    id: int
    video_url: str
    video_title: Optional[str]
    format: str
    quality: str
    status: str
    error_message: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}
