"""Pet Flâneur comic generation."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException

from models.schemas import (
    ExportRequest,
    ExportResponse,
    GenerateComicRequest,
    GenerateComicResponse,
    Panel,
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


def _pick_variant(selected: list[dict], wp_type: str, idx: int) -> dict:
    """Choose the selected variant whose pose best fits this stop's type."""
    keywords = TYPE_KEYWORDS.get(wp_type, [])
    best, best_score = None, -1
    for v in selected:
        pose = v.get("pose_prompt", "").lower()
        score = sum(1 for k in keywords if k in pose)
        if score > best_score:
            best, best_score = v, score
    if best is None or best_score <= 0:
        return selected[idx % len(selected)]
    return best


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

    panels: list[Panel] = []
    panel_paths: list[str] = []
    for i, wp in enumerate(waypoints):
        location = wp.name or f"Stop {i + 1}"
        scene_path = os.path.join(comic_dir, f"scene_{i:02d}.png")
        # 1) fetch street view (stub: themed scene by place type)
        streetview.fetch_street_view(wp.lat, wp.lng, wp.type, location, scene_path)
        # 2) tintinify (stub: pass-through)
        scene_path = comfy.tintinify_scene(scene_path)
        # 3) composite the pet character into the scene (Pillow compositor)
        variant = _pick_variant(selected, wp.type, i)
        panel_path = os.path.join(comic_dir, f"panel_{i:02d}.png")
        make_panel(scene_path, pet["image_path"], location, panel_path, index=i)
        panel_paths.append(panel_path)
        panels.append(
            Panel(
                order=i,
                image_url=f"/static/generated/comics/{comic_id}/panel_{i:02d}.png",
                location_name=location,
                type=wp.type,
            )
        )

    # Keep the panel paths so /export can build a print template on demand
    # (strip or zine, with blank-cell captions chosen at download time).
    COMICS[comic_id] = {"dir": comic_dir, "panel_paths": panel_paths}

    return GenerateComicResponse(comic_id=comic_id, panels=panels)


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
