"""Pillow-based comic-panel compositing.

This is the *real* (non-AI) compositing used for the demo: it drops the user's
pet (comic-treated) into a scene. No text or frame is baked into the image — the
location label is shown in the UI under each panel, and the soft frame is the
frontend `pv-frame`; print templates stay text-free to match the layouts. The
ComfyUI composite step stays stubbed for the future pipeline.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

from .placeholders import _comicify, _draw_paw

RING_COLORS = ["#FFD700", "#FF5C35", "#FF69B4", "#7ED957", "#5EC5FF", "#9C8CF5"]


def make_panel(
    scene_path: str,
    pet_image_path: str | None,
    caption: str,  # kept for signature stability; label is shown in the UI, not baked
    out_path: str,
    index: int = 0,
) -> str:
    """Composite the pet (comic-treated circle) into the scene. Saves PNG."""
    scene = Image.open(scene_path).convert("RGB")
    w, h = scene.size
    d = ImageDraw.Draw(scene)

    # Pet character — comic-treated circle with a sticker ring + drop shadow.
    diameter = int(h * 0.46)
    cx, cy = int(w * 0.5), int(h * 0.66)
    d.ellipse((cx - diameter // 2, cy - diameter // 2 + 10, cx + diameter // 2, cy + diameter // 2 + 18),
              fill=(0, 0, 0, 60))
    ring = diameter + 16
    d.ellipse((cx - ring // 2, cy - ring // 2, cx + ring // 2, cy + ring // 2),
              fill=RING_COLORS[index % len(RING_COLORS)], outline="#FFFFFF", width=6)
    placed = False
    if pet_image_path and os.path.exists(pet_image_path):
        try:
            with Image.open(pet_image_path) as src:
                pet = _comicify(src, diameter)
            scene.paste(pet, (cx - diameter // 2, cy - diameter // 2), pet)
            placed = True
        except Exception:  # noqa: BLE001
            placed = False
    if not placed:
        # Description-only (or unreadable photo): chunky white paw inside the ring.
        _draw_paw(d, cx, cy, diameter, "#FFFFFF")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene.save(out_path, "PNG")
    return out_path
