"""Pillow-based comic-panel compositing.

This is the *real* (non-AI) compositing used for the demo: it drops the user's
pet (comic-treated) into a scene and frames it like a Tintin panel with a
caption bar. The ComfyUI composite step stays stubbed for the future pipeline.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

from .placeholders import _comicify, _load_font

INK = "#1A1A2E"
RING_COLORS = ["#FFD700", "#FF5C35", "#FF69B4", "#7ED957", "#5EC5FF", "#9C8CF5"]


def make_panel(
    scene_path: str,
    pet_image_path: str | None,
    caption: str,
    out_path: str,
    index: int = 0,
) -> str:
    """Composite the pet into the scene + caption bar + comic frame. Saves PNG."""
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
    if pet_image_path and os.path.exists(pet_image_path):
        try:
            with Image.open(pet_image_path) as src:
                pet = _comicify(src, diameter)
            scene.paste(pet, (cx - diameter // 2, cy - diameter // 2), pet)
        except Exception:  # noqa: BLE001
            pass

    # Caption bar.
    font = _load_font(24)
    bar_h = 56
    d.rectangle((0, h - bar_h, w, h), fill=INK)
    cap = caption if len(caption) <= 46 else caption[:43] + "…"
    d.text((20, h - bar_h + 15), cap, font=font, fill="#FFFFFF")

    # Comic frame.
    d.rectangle((3, 3, w - 4, h - 4), outline=INK, width=6)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    scene.save(out_path, "PNG")
    return out_path
