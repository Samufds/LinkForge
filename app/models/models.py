from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class URL(Base):
    """Stores original URLs and their short codes."""
    __tablename__ = "urls"

    id = Column(Integer, primary_key=True, index=True)
    original_url = Column(Text, nullable=False)
    short_code = Column(String(20), unique=True, index=True, nullable=False)
    custom_alias = Column(String(50), unique=True, index=True, nullable=True)
    click_count = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    @property
    def effective_code(self) -> str:
        """Returns custom alias if set, otherwise the generated short code."""
        return self.custom_alias or self.short_code


class DownloadJob(Base):
    """Tracks YouTube download requests."""
    __tablename__ = "download_jobs"

    id = Column(Integer, primary_key=True, index=True)
    video_url = Column(Text, nullable=False)
    video_title = Column(String(500), nullable=True)
    video_id = Column(String(50), nullable=True)
    format = Column(String(10), default="mp4", nullable=False)   # mp4 | mp3
    quality = Column(String(20), default="best", nullable=False)  # best | 720p | 480p | 360p
    status = Column(String(20), default="pending", nullable=False)  # pending | processing | done | failed
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
