"""Petventures backend — FastAPI app entry point.

Run from the backend/ directory:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

import os


def _load_dotenv() -> None:
    """Load the nearest .env (searching up from here to the repo root) into the
    environment, without adding a dependency. Existing env vars win."""
    here = os.path.dirname(os.path.abspath(__file__))
    for _ in range(5):
        envp = os.path.join(here, ".env")
        if os.path.isfile(envp):
            with open(envp, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            return
        parent = os.path.dirname(here)
        if parent == here:
            break
        here = parent


_load_dotenv()

from fastapi import FastAPI  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402

from routers import flaneur, pet  # noqa: E402

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
app.include_router(flaneur.router)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "petventures"}
