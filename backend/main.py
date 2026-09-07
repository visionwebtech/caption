"""
CaptionFlow — FastAPI Main Entry Point
This is the file you run to start the backend server.
"""

import sys
import os

# Make sure Python can find all our modules
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from config import settings
from routes import upload, transcribe, captions, export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    print("=" * 50)
    print("  CaptionFlow Backend Starting")
    print(f"  Whisper Model: {settings.whisper_model}")
    print(f"  Upload Dir:    {settings.upload_dir}")
    print(f"  Output Dir:    {settings.output_dir}")
    print(f"  Frontend URL:  {settings.frontend_url}")
    print("=" * 50)
    yield
    print("CaptionFlow Backend stopped.")


app = FastAPI(
    title="CaptionFlow API",
    description="AI-powered auto-caption video editor backend",
    version="1.0.0",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow the React frontend (running on localhost:5173) to call our API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_url,
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routes ───────────────────────────────────────────────────────────────────
app.include_router(upload.router)
app.include_router(transcribe.router)
app.include_router(captions.router)
app.include_router(export.router)


# ─── Health Check ─────────────────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    """
    Simple health check endpoint.
    Open http://localhost:8000/api/health in your browser to verify the backend is running.
    """
    import shutil
    return {
        "status": "ok",
        "whisper_model": settings.whisper_model,
        "ffmpeg_available": bool(shutil.which("ffmpeg")),
        "version": "1.0.0",
    }


@app.get("/")
async def root():
    return {
        "message": "CaptionFlow API is running!",
        "docs": "http://localhost:8000/docs",
        "health": "http://localhost:8000/api/health",
    }
