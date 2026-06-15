"""Mapillary coverage tiles + photo search — proxied so the token stays server-side.

The frontend's map adds a vector source pointing at `/api/mapillary/coverage/
{z}/{x}/{y}`; this router fetches the matching Mapillary vector tile with the
`.env` token and streams it back. That way the token never ships in the browser
bundle. `/status` lets the UI know whether to show the coverage toggle at all.

`/photos` returns ranked Mapillary photo candidates near a point, so the route
step can let users pick a background before comic generation.
"""

from __future__ import annotations

import json
import math
import os
import urllib.parse
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


MAPILLARY_GRAPH = "https://graph.mapillary.com/images"
SEARCH_RADII_M = (60, 150, 350)
MAX_PHOTOS = 6


def _bbox(lat: float, lng: float, meters: float) -> str:
    dlat = meters / 111_320.0
    dlng = meters / (111_320.0 * max(0.01, math.cos(math.radians(lat))))
    return f"{lng - dlng:.6f},{lat - dlat:.6f},{lng + dlng:.6f},{lat + dlat:.6f}"


@router.get("/photos")
def photos(lat: float, lng: float) -> dict:
    """Return ranked Mapillary photo candidates near a point."""
    token = _token()
    if not token:
        return {"photos": []}

    fields = "id,computed_geometry,geometry,compass_angle,captured_at,thumb_256_url,thumb_1024_url,is_pano"
    data = []
    try:
        for meters in SEARCH_RADII_M:
            qs = urllib.parse.urlencode({"fields": fields, "bbox": _bbox(lat, lng, meters), "limit": 40})
            url = f"{MAPILLARY_GRAPH}?access_token={token}&{qs}"
            req = urllib.request.Request(url, headers={"User-Agent": "petagonist/0.1"})
            with urllib.request.urlopen(req, timeout=15) as r:
                data = (json.load(r) or {}).get("data", [])
            if data:
                break
    except Exception:
        return {"photos": []}

    if not data:
        return {"photos": []}

    def dist(c):
        g = c.get("computed_geometry") or c.get("geometry") or {}
        co = g.get("coordinates")
        return ((co[1] - lat) ** 2 + (co[0] - lng) ** 2) if co else 9e9

    ranked = sorted(data, key=lambda c: (1 if c.get("is_pano") else 0, dist(c), -(c.get("captured_at") or 0)))

    results = []
    for c in ranked[:MAX_PHOTOS]:
        thumb = c.get("thumb_256_url")
        full = c.get("thumb_1024_url")
        if not thumb or not full:
            continue
        results.append({
            "id": str(c["id"]),
            "thumb_url": thumb,
            "full_url": full,
            "is_pano": c.get("is_pano", False),
        })

    return {"photos": results}
