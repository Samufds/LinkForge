from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.schemas import URLCreate, URLResponse, URLStats
from app.services import url_service

router = APIRouter(prefix="/api/urls", tags=["URL Shortener"])


@router.post("/", response_model=URLResponse, status_code=status.HTTP_201_CREATED)
def create_url(payload: URLCreate, db: Session = Depends(get_db)):
    """Create a shortened URL, optionally with a custom alias."""
    url_obj = url_service.create_short_url(db, payload)
    data = url_obj.__dict__.copy()
    data["short_url"] = url_service.build_short_url(url_obj.effective_code)
    return URLResponse(**data)


@router.get("/", response_model=list[URLResponse])
def list_urls(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    """List all shortened URLs (most recent first)."""
    urls = url_service.list_urls(db, skip=skip, limit=limit)
    result = []
    for u in urls:
        data = u.__dict__.copy()
        data["short_url"] = url_service.build_short_url(u.effective_code)
        result.append(URLResponse(**data))
    return result


@router.get("/{code}/stats", response_model=URLStats)
def get_stats(code: str, db: Session = Depends(get_db)):
    """Get click statistics for a short URL."""
    url_obj = url_service.get_url_stats(db, code)
    return URLStats(
        short_code=url_obj.effective_code,
        original_url=url_obj.original_url,
        click_count=url_obj.click_count,
        is_active=url_obj.is_active,
        created_at=url_obj.created_at,
    )


@router.delete("/{code}", status_code=status.HTTP_204_NO_CONTENT)
def deactivate_url(code: str, db: Session = Depends(get_db)):
    """Deactivate (soft-delete) a shortened URL."""
    url_service.deactivate_url(db, code)
