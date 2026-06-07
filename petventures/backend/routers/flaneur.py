"""Pet Flâneur comic generation."""

from __future__ import annotations

import os
import uuid

from fastapi import APIRouter, HTTPException

from models.schemas import GenerateComicRequest, GenerateComicResponse, Panel
from services import layout, streetview
from services.comfyui_client import ComfyUIClient
from services.compositor import make_panel

from .pet import GENERATED_DIR, PETS, comfy as _comfy  # reuse pet store + client

router = APIRouter(prefix="/api/flaneur", tags=["flaneur"])

comfy: ComfyUIClient = _comfy

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
    waypoints = sorted(req.waypoints, key=lambda w: w.order)

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

    # 4) lay out a downloadable strip + PDF
    strip_path = os.path.join(comic_dir, "strip.png")
    pdf_path = os.path.join(comic_dir, "comic.pdf")
    layout.build_strip(panel_paths, strip_path, orientation="horizontal")
    layout.build_pdf(panel_paths, pdf_path)

    return GenerateComicResponse(
        comic_id=comic_id,
        panels=panels,
        strip_url=f"/static/generated/comics/{comic_id}/strip.png",
        pdf_url=f"/static/generated/comics/{comic_id}/comic.pdf",
    )
