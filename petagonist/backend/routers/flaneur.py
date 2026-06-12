"""Pet Flâneur comic generation."""

from __future__ import annotations

import json
import os
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from models.schemas import (
    ExportRequest,
    ExportResponse,
    GenerateComicRequest,
    GenerateComicResponse,
    Panel,
    RegeneratePanelRequest,
)
from services import layout, streetview
from services.comfyui_client import ComfyUIClient
from services.compositor import make_panel

from .pet import GENERATED_DIR, PETS, comfy as _comfy  # reuse pet store + client

router = APIRouter(prefix="/api/flaneur", tags=["flaneur"])

comfy: ComfyUIClient = _comfy

MAX_STOPS = 8  # caps the comic at 8 panels (one printable page)

# Generated comics, keyed by comic_id, so /export can re-lay the panels into a
# print template at download time (with any blank-cell captions). In-memory for
# the demo; the panel PNGs themselves persist on disk.
COMICS: dict[str, dict] = {}

# Which pose keywords suit each place type — lets the route theme the comic.
TYPE_KEYWORDS = {
    "water": ["water", "bridge", "promenade", "fountain", "waterfront", "river"],
    "park": ["tree", "park", "pigeon", "bench", "flower", "courtyard", "fountain", "planter"],
    "plaza": ["plaza", "pigeon", "crosswalk", "musician", "market", "fountain", "square"],
    "street": ["street", "sidewalk", "alley", "crosswalk", "lamppost", "tram", "bus", "shop", "cafe", "cobblestone"],
    "building": ["building", "balcony", "rooftop", "apartment", "window", "shop", "cafe", "cathedral", "mailbox"],
    "place": [],
}


def _pick_variant(selected: list[dict], wp_type: str, order: int, scene_idx: int) -> dict:
    """Choose which character/pose stars in a panel.

    First roll (scene_idx 0): the selected variant whose pose best fits the
    stop's type. Re-rolls rotate through the rest, so regenerating swaps the
    character/pose too (alongside the new scene).
    """
    if scene_idx > 0:
        return selected[(order + scene_idx) % len(selected)]
    keywords = TYPE_KEYWORDS.get(wp_type, [])
    best, best_score = None, -1
    for v in selected:
        pose = v.get("pose_prompt", "").lower()
        score = sum(1 for k in keywords if k in pose)
        if score > best_score:
            best, best_score = v, score
    if best is None or best_score <= 0:
        return selected[order % len(selected)]
    return best


def _panel_url(comic_id: str, path: str) -> str:
    return f"/static/generated/comics/{comic_id}/{os.path.basename(path)}"


def _build_panel(comic: dict, order: int, scene_idx: int) -> Panel:
    """(Re)build a single panel at the given scene index and return its Panel.

    Updates the stored per-panel state + panel_paths so exports use the latest.
    The `scene_idx` is the re-roll counter — it seeds the scene source (today a
    varied placeholder; later candidate #scene_idx from Mapillary) and rotates
    the character pose.
    """
    meta = comic["panels"][order]
    wp = meta["wp"]
    location = wp["name"] or f"Stop {order + 1}"
    suffix = f"{order:02d}_v{scene_idx}"

    # 1) scene source — Mapillary street photo (with drawn fallback).
    scene_path = os.path.join(comic["dir"], f"scene_{suffix}.png")
    seed = (order * 1000 + scene_idx) & 0xFFFF
    streetview.fetch_street_view(wp["lat"], wp["lng"], wp["type"], location, scene_path, seed=seed)
    # 2+3) tintinify scene + composite pet in one ComfyUI pass.
    variant = _pick_variant(comic["selected"], wp["type"], order, scene_idx)
    panel_path = os.path.join(comic["dir"], f"panel_{suffix}.png")
    variant_path = variant.get("path")
    if variant_path and os.path.exists(variant_path):
        result = comfy.composite_panel(scene_path, variant_path, panel_path, seed=seed)
        if result != panel_path:
            make_panel(scene_path, comic["pet"]["image_path"], location, panel_path, index=order + scene_idx)
    else:
        make_panel(scene_path, comic["pet"]["image_path"], location, panel_path, index=order + scene_idx)

    meta["scene_idx"] = scene_idx
    comic["panel_paths"][order] = panel_path
    return Panel(order=order, image_url=_panel_url(comic["comic_id"], panel_path), location_name=location, type=wp["type"])


@router.post("/generate", response_model=GenerateComicResponse)
async def generate_comic(req: GenerateComicRequest) -> GenerateComicResponse:
    pet = PETS.get(req.pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Unknown pet — upload first.")
    if len(req.waypoints) < 2:
        raise HTTPException(status_code=400, detail="Add at least 2 waypoints.")

    stored = pet.get("variants", {})
    selected = [stored[v] for v in req.selected_variant_ids if v in stored]
    if not selected:
        raise HTTPException(status_code=400, detail="Pick at least one character first.")

    comic_id = uuid.uuid4().hex[:12]
    comic_dir = os.path.join(GENERATED_DIR, "comics", comic_id)
    waypoints = sorted(req.waypoints, key=lambda w: w.order)[:MAX_STOPS]

    comic = {
        "comic_id": comic_id,
        "dir": comic_dir,
        "pet": pet,
        "selected": selected,
        "panel_paths": [None] * len(waypoints),
        "panels": [
            {"order": i, "wp": {"lat": wp.lat, "lng": wp.lng, "type": wp.type, "name": wp.name}, "scene_idx": 0}
            for i, wp in enumerate(waypoints)
        ],
    }
    COMICS[comic_id] = comic

    panels = [_build_panel(comic, i, 0) for i in range(len(waypoints))]
    return GenerateComicResponse(comic_id=comic_id, panels=panels)


@router.post("/generate-stream")
async def generate_comic_stream(req: GenerateComicRequest):
    """SSE endpoint — streams each comic panel as it finishes."""
    pet = PETS.get(req.pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Unknown pet — upload first.")
    if len(req.waypoints) < 2:
        raise HTTPException(status_code=400, detail="Add at least 2 waypoints.")

    stored = pet.get("variants", {})
    selected = [stored[v] for v in req.selected_variant_ids if v in stored]
    if not selected:
        raise HTTPException(status_code=400, detail="Pick at least one character first.")

    comic_id = uuid.uuid4().hex[:12]
    comic_dir = os.path.join(GENERATED_DIR, "comics", comic_id)
    waypoints = sorted(req.waypoints, key=lambda w: w.order)[:MAX_STOPS]

    comic = {
        "comic_id": comic_id,
        "dir": comic_dir,
        "pet": pet,
        "selected": selected,
        "panel_paths": [None] * len(waypoints),
        "panels": [
            {"order": i, "wp": {"lat": wp.lat, "lng": wp.lng, "type": wp.type, "name": wp.name}, "scene_idx": 0}
            for i, wp in enumerate(waypoints)
        ],
    }
    COMICS[comic_id] = comic

    def event_stream():
        total = len(waypoints)
        yield f"data: {json.dumps({'type': 'start', 'comic_id': comic_id, 'total': total})}\n\n"

        for i in range(total):
            panel = _build_panel(comic, i, 0)
            panel_data = {
                "type": "panel",
                "index": i,
                "total": total,
                "panel": {
                    "order": panel.order,
                    "image_url": panel.image_url,
                    "location_name": panel.location_name,
                    "type": panel.type,
                },
            }
            yield f"data: {json.dumps(panel_data)}\n\n"

        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/regenerate-panel", response_model=Panel)
async def regenerate_panel(req: RegeneratePanelRequest) -> Panel:
    """Re-roll a single panel — a new scene (and rotated pose) for that stop."""
    comic = COMICS.get(req.comic_id)
    if comic is None:
        raise HTTPException(status_code=404, detail="Unknown comic — generate one first.")
    if req.order < 0 or req.order >= len(comic["panels"]):
        raise HTTPException(status_code=400, detail="No such panel.")
    next_idx = comic["panels"][req.order]["scene_idx"] + 1
    return _build_panel(comic, req.order, next_idx)


@router.post("/export", response_model=ExportResponse)
async def export_comic(req: ExportRequest) -> ExportResponse:
    """Render the chosen printable 16:9 template (strip / zine) and return its URL."""
    comic = COMICS.get(req.comic_id)
    if comic is None:
        raise HTTPException(status_code=404, detail="Unknown comic — generate one first.")

    template = req.template if req.template in ("strip", "zine") else "strip"
    fmt = req.format if req.format in ("pdf", "png") else "pdf"
    filename = f"{template}.{fmt}"
    out_path = os.path.join(comic["dir"], filename)

    layout.build_print_template(comic["panel_paths"], req.captions, template, out_path, fmt)
    comic_id = req.comic_id
    return ExportResponse(url=f"/static/generated/comics/{comic_id}/{filename}")
