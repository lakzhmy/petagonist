"""Pet Flâneur comic generation."""

from __future__ import annotations

import io
import json
import logging
import os
import urllib.request
import uuid

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from PIL import Image, ImageEnhance, ImageOps

log = logging.getLogger(__name__)

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


def _download_scene(url: str, out_path: str, size: tuple[int, int] = (900, 600)) -> None:
    """Download a Mapillary photo by its thumb URL and save it locally."""
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "petagonist/0.1"})
        with urllib.request.urlopen(req, timeout=20) as r:
            photo = Image.open(io.BytesIO(r.read())).convert("RGB")
        photo = ImageOps.fit(photo, size, Image.LANCZOS)
        photo = ImageEnhance.Color(photo).enhance(1.25)
        photo = ImageEnhance.Contrast(photo).enhance(1.08)
        photo = ImageOps.posterize(photo, 5)
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        photo.save(out_path, "PNG")
    except Exception:
        log.exception("Failed to download pre-selected scene")


def _pick_variant(selected: list[dict], wp_type: str, order: int, variant_idx: int) -> dict:
    """Choose which character/pose stars in a panel.

    First roll (variant_idx 0): the selected variant whose pose best fits the
    stop's type. Higher variant_idx values rotate through the rest.
    """
    if variant_idx > 0:
        return selected[(order + variant_idx) % len(selected)]
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


def _build_panel(comic: dict, order: int, scene_idx: int, variant_idx: int) -> Panel:
    """(Re)build a single panel and return its Panel.

    `scene_idx` controls which Mapillary photo candidate is used.
    `variant_idx` controls which character variant / pose is used.
    """
    meta = comic["panels"][order]
    wp = meta["wp"]
    location = wp["name"] or f"Stop {order + 1}"
    suffix = f"{order:02d}_s{scene_idx}_c{variant_idx}"

    # 1) scene source — pre-selected Mapillary photo, or search + fallback.
    scene_path = os.path.join(comic["dir"], f"scene_{order:02d}_s{scene_idx}.png")
    seed = (order * 1000 + scene_idx) & 0xFFFF

    prev_scene = meta.get("_scene_path")
    if prev_scene and os.path.exists(prev_scene) and scene_idx == meta.get("scene_idx", 0):
        scene_path = prev_scene
    elif wp.get("scene_url") and scene_idx == 0:
        _download_scene(wp["scene_url"], scene_path)
    else:
        streetview.fetch_street_view(wp["lat"], wp["lng"], wp["type"], location, scene_path, seed=seed)

    # If the scene file wasn't created (no Mapillary coverage, network error),
    # generate a simple placeholder so downstream steps don't crash.
    if not os.path.exists(scene_path):
        log.warning("Scene missing for stop %d — creating placeholder", order)
        os.makedirs(os.path.dirname(scene_path), exist_ok=True)
        Image.new("RGB", (900, 600), (200, 210, 220)).save(scene_path, "PNG")

    # 2+3) tintinify scene + composite pet in one ComfyUI pass.
    variant = _pick_variant(comic["selected"], wp["type"], order, variant_idx)
    panel_path = os.path.join(comic["dir"], f"panel_{suffix}.png")
    comfy_seed = (order * 1000 + scene_idx * 100 + variant_idx) & 0xFFFF
    variant_path = variant.get("path")
    pet_description = comic["pet"].get("description", "")
    pose_prompt = variant.get("pose_prompt", "")
    if variant_path and os.path.exists(variant_path):
        result = comfy.composite_panel(
            scene_path, variant_path, panel_path, seed=comfy_seed,
            pet_description=pet_description, pose_prompt=pose_prompt,
        )
        if result != panel_path:
            make_panel(scene_path, comic["pet"]["image_path"], location, panel_path, index=order + variant_idx)
    else:
        make_panel(scene_path, comic["pet"]["image_path"], location, panel_path, index=order + variant_idx)

    meta["scene_idx"] = scene_idx
    meta["variant_idx"] = variant_idx
    meta["_scene_path"] = scene_path
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
            {"order": i, "wp": {"lat": wp.lat, "lng": wp.lng, "type": wp.type, "name": wp.name, "scene_url": wp.scene_url}, "scene_idx": 0, "variant_idx": 0}
            for i, wp in enumerate(waypoints)
        ],
    }
    COMICS[comic_id] = comic

    panels = [_build_panel(comic, i, 0, 0) for i in range(len(waypoints))]
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
            {"order": i, "wp": {"lat": wp.lat, "lng": wp.lng, "type": wp.type, "name": wp.name, "scene_url": wp.scene_url}, "scene_idx": 0, "variant_idx": 0}
            for i, wp in enumerate(waypoints)
        ],
    }
    COMICS[comic_id] = comic

    def event_stream():
        total = len(waypoints)
        yield f"data: {json.dumps({'type': 'start', 'comic_id': comic_id, 'total': total})}\n\n"

        for i in range(total):
            panel = _build_panel(comic, i, 0, 0)
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
    """Re-roll a single panel. mode controls what changes:
    - "all": new background + new character (default, legacy behavior)
    - "background": new Mapillary photo, same character variant
    - "character": same background, different character variant / seed
    """
    comic = COMICS.get(req.comic_id)
    if comic is None:
        raise HTTPException(status_code=404, detail="Unknown comic — generate one first.")
    if req.order < 0 or req.order >= len(comic["panels"]):
        raise HTTPException(status_code=400, detail="No such panel.")

    meta = comic["panels"][req.order]
    cur_scene = meta.get("scene_idx", 0)
    cur_variant = meta.get("variant_idx", 0)

    if req.mode == "background":
        return _build_panel(comic, req.order, cur_scene + 1, cur_variant)
    elif req.mode == "character":
        return _build_panel(comic, req.order, cur_scene, cur_variant + 1)
    else:
        return _build_panel(comic, req.order, cur_scene + 1, cur_variant + 1)


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
