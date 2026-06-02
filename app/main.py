from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
from sqlalchemy.orm import Session
from contextlib import asynccontextmanager

from app.core.database import engine, get_db, Base
from app.models import models  # noqa — ensures models are registered
from app.routers import urls, youtube
from app.services import url_service


# ─────────────────────────────────────────────
#  Lifespan: create DB tables on startup
# ─────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables if they don't exist (use Alembic for migrations in production)
    Base.metadata.create_all(bind=engine)
    print("✅  Database tables ready.")
    yield


# ─────────────────────────────────────────────
#  App
# ─────────────────────────────────────────────

app = FastAPI(
    title="LinkForge",
    description="URL Shortener + YouTube Downloader built with FastAPI, PostgreSQL & SQLAlchemy",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# ─────────────────────────────────────────────
#  Include routers
# ─────────────────────────────────────────────

app.include_router(urls.router)
app.include_router(youtube.router)


# ─────────────────────────────────────────────
#  Redirect route  /{code}  →  original URL
# ─────────────────────────────────────────────

@app.get("/{code}", include_in_schema=False)
def redirect_short_url(code: str, db: Session = Depends(get_db)):
    """Resolve a short code and redirect the user."""
    # Don't intercept known routes
    if code in ("docs", "redoc", "openapi.json", "static", "api"):
        raise HTTPException(status_code=404, detail="Not found")

    url_obj = url_service.get_url_by_code(db, code)
    url_service.increment_click(db, url_obj)
    return RedirectResponse(url=url_obj.original_url, status_code=301)


# ─────────────────────────────────────────────
#  Frontend
# ─────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def serve_frontend(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})
