"""Mapillary coverage tiles — proxied so the token stays server-side.

The frontend's map adds a vector source pointing at `/api/mapillary/coverage/
{z}/{x}/{y}`; this router fetches the matching Mapillary vector tile with the
`.env` token and streams it back. That way the token never ships in the browser
bundle. `/status` lets the UI know whether to show the coverage toggle at all.
"""

from __future__ import annotations

import os
import urllib.request

from fastapi import APIRouter, HTTPException, Response

router = APIRouter(prefix="/api/mapillary", tags=["mapillary"])

# Mapillary public vector tiles (coverage): layers `overview`/`sequence`/`image`.
TILE_URL = "https://tiles.mapillary.com/maps/vtp/mly1_public/2/{z}/{x}/{y}"
MVT_MIME = "application/vnd.mapbox-vector-tile"


def _token() -> str | None:
    return os.environ.get("MAPILLARY_TOKEN") or os.environ.get("MapillaryToken")


@router.get("/status")
def status() -> dict:
    """Whether coverage tiles are available (i.e. a token is configured)."""
    return {"enabled": bool(_token())}


@router.get("/coverage/{z}/{x}/{y}")
def coverage(z: int, x: int, y: int) -> Response:
    """Proxy one Mapillary coverage vector tile."""
    token = _token()
    if not token:
        raise HTTPException(status_code=404, detail="Mapillary token not configured.")
    url = f"{TILE_URL.format(z=z, x=x, y=y)}?access_token={token}"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "petagonist/0.1"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = r.read()
    except Exception:  # noqa: BLE001 — empty/missing tile → let the map treat it as blank
        return Response(status_code=204)
    return Response(
        content=data,
        media_type=MVT_MIME,
        headers={"Cache-Control": "public, max-age=86400"},
    )
