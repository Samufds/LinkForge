import shortuuid
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from app.models.models import URL
from app.schemas.schemas import URLCreate
from app.core.config import get_settings

settings = get_settings()


def generate_short_code(length: int = None) -> str:
    length = length or settings.short_code_length
    return shortuuid.ShortUUID().random(length=length)


def create_short_url(db: Session, payload: URLCreate) -> URL:
    """Create a new shortened URL, with optional custom alias."""

    original = str(payload.original_url)

    # Check custom alias availability
    if payload.custom_alias:
        existing = db.query(URL).filter(URL.custom_alias == payload.custom_alias).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Alias '{payload.custom_alias}' is already taken.",
            )

    # Generate unique short code
    for _ in range(5):  # Retry up to 5 times on collision
        short_code = generate_short_code()
        if not db.query(URL).filter(URL.short_code == short_code).first():
            break
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate a unique short code. Try again.",
        )

    url_obj = URL(
        original_url=original,
        short_code=short_code,
        custom_alias=payload.custom_alias,
    )
    db.add(url_obj)
    db.commit()
    db.refresh(url_obj)
    return url_obj


def get_url_by_code(db: Session, code: str) -> URL:
    """Resolve a short code or alias to its URL record."""
    url_obj = (
        db.query(URL)
        .filter(
            (URL.short_code == code) | (URL.custom_alias == code),
            URL.is_active == True,
        )
        .first()
    )
    if not url_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Short URL '{code}' not found or has been deactivated.",
        )
    return url_obj


def increment_click(db: Session, url_obj: URL) -> None:
    url_obj.click_count += 1
    db.commit()


def get_url_stats(db: Session, code: str) -> URL:
    return get_url_by_code(db, code)


def list_urls(db: Session, skip: int = 0, limit: int = 50) -> list[URL]:
    return db.query(URL).order_by(URL.created_at.desc()).offset(skip).limit(limit).all()


def deactivate_url(db: Session, code: str) -> URL:
    url_obj = get_url_by_code(db, code)
    url_obj.is_active = False
    db.commit()
    db.refresh(url_obj)
    return url_obj


def build_short_url(code: str) -> str:
    return f"{settings.base_url}/{code}"
