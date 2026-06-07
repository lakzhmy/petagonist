"""Comic-strip layout: combine panels into a downloadable strip PNG + PDF."""

from __future__ import annotations

import os

from PIL import Image

GAP = 18
PAD = 24
BG = "#4A2FBD"  # grape


def build_strip(panel_paths: list[str], out_path: str, orientation: str = "horizontal") -> str:
    """Stitch panels into a single image (horizontal strip or vertical zine)."""
    panels = [Image.open(p).convert("RGB") for p in panel_paths]
    if not panels:
        raise ValueError("no panels to lay out")

    if orientation == "vertical":
        w = max(p.width for p in panels) + PAD * 2
        h = sum(p.height for p in panels) + GAP * (len(panels) - 1) + PAD * 2
        canvas = Image.new("RGB", (w, h), BG)
        y = PAD
        for p in panels:
            canvas.paste(p, ((w - p.width) // 2, y))
            y += p.height + GAP
    else:
        h = max(p.height for p in panels) + PAD * 2
        w = sum(p.width for p in panels) + GAP * (len(panels) - 1) + PAD * 2
        canvas = Image.new("RGB", (w, h), BG)
        x = PAD
        for p in panels:
            canvas.paste(p, (x, (h - p.height) // 2))
            x += p.width + GAP

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    canvas.save(out_path, "PNG")
    return out_path


def build_pdf(panel_paths: list[str], out_path: str) -> str:
    """Save all panels into a single PDF (one panel per page)."""
    panels = [Image.open(p).convert("RGB") for p in panel_paths]
    if not panels:
        raise ValueError("no panels to lay out")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    panels[0].save(out_path, "PDF", save_all=True, append_images=panels[1:], resolution=150)
    return out_path
