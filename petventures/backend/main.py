"""Petventures backend — FastAPI app entry point.

Run from the backend/ directory:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from routers import pet

BACKEND_ROOT = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BACKEND_ROOT, "static")
# Ensure the served directories exist on a fresh checkout.
os.makedirs(os.path.join(STATIC_DIR, "uploads"), exist_ok=True)
os.makedirs(os.path.join(STATIC_DIR, "generated"), exist_ok=True)

app = FastAPI(title="Petventures API", version="0.1.0")

# Allow the Vite dev server to call us directly (in addition to its proxy).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve uploaded + generated images.
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(pet.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "petventures"}
