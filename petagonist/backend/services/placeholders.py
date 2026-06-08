"""On-brand placeholder image generation with Pillow.

Until the real ComfyUI / Tintin LoRA pipeline is connected, these functions
produce images that *look intentional* rather than like gray boxes: bold
palette-colored cards, the user's own pet posterized into a circular "comic"
inset, the pose prompt as a caption, and a little sparkle accent.
"""

from __future__ import annotations

import os
import textwrap

from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

# --- Petagonist palette (mirrors the frontend design tokens) --------------
PALETTE = [
    ("#FF5C35", "#FFFFFF"),  # tang  / white text
    ("#4A2FBD", "#FFFFFF"),  # grape / white
    ("#FF69B4", "#FFFFFF"),  # bubble/ white
    ("#7ED957", "#1A1A2E"),  # lime  / ink
    ("#FFD700", "#1A1A2E"),  # sun   / ink
    ("#5EC5FF", "#1A1A2E"),  # sky   / ink
]
INK = "#1A1A2E"
CREAM = "#F5F0EB"


def _load_font(size: int, bold: bool = True) -> ImageFont.FreeTypeFont:
    """Best-effort TrueType font across platforms; falls back to default."""
    candidates = (
        ["C:/Windows/Fonts/arialbd.ttf", "C:/Windows/Fonts/segoeuib.ttf"]
        if bold
        else ["C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/segoeui.ttf"]
    )
    candidates += [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
        if bold
        else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _comicify(src: Image.Image, diameter: int) -> Image.Image:
    """Crop to a circle and apply a cheap 'comic' treatment (posterize +
    punchy saturation) as a stand-in for the real Tintin render."""
    img = ImageOps.exif_transpose(src).convert("RGB")
    img = ImageOps.fit(img, (diameter, diameter), Image.LANCZOS)
    img = ImageEnhance.Color(img).enhance(1.5)
    img = ImageEnhance.Contrast(img).enhance(1.15)
    img = ImageOps.posterize(img, 4)  # flatten tones toward ligne claire

    # Circular alpha mask
    mask = Image.new("L", (diameter, diameter), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, diameter, diameter), fill=255)
    out = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _draw_sparkle(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill: str) -> None:
    """A chunky 4-point star, matching the UI sparkle motif."""
    thin = max(2, r // 4)
    draw.polygon(
        [(cx, cy - r), (cx + thin, cy - thin), (cx + r, cy),
         (cx + thin, cy + thin), (cx, cy + r), (cx - thin, cy + thin),
         (cx - r, cy), (cx - thin, cy - thin)],
        fill=fill,
    )


def _rounded_card(size: int, bg: str) -> Image.Image:
    card = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    ImageDraw.Draw(card).rounded_rectangle(
        (0, 0, size - 1, size - 1), radius=size // 10, fill=bg
    )
    return card


def generate_variant_card(
    pet_image_path: str | None,
    pose_prompt: str,
    out_path: str,
    index: int = 0,
    size: int = 512,
) -> str:
    """Render one character-variant card and save it as PNG.

    Returns the output path. Each variant gets a different palette color so a
    grid of them reads as rich and varied.
    """
    bg, text_color = PALETTE[index % len(PALETTE)]
    card = _rounded_card(size, bg)
    draw = ImageDraw.Draw(card)

    # Pet inset (their actual photo, comic-treated) or a fallback paw glyph.
    diameter = int(size * 0.52)
    cx, cy = size // 2, int(size * 0.4)
    # White ring behind the inset for that sticker-y pop.
    ring = diameter + 18
    draw.ellipse(
        (cx - ring // 2, cy - ring // 2, cx + ring // 2, cy + ring // 2),
        fill="#FFFFFF",
    )
    if pet_image_path and os.path.exists(pet_image_path):
        try:
            with Image.open(pet_image_path) as src:
                inset = _comicify(src, diameter)
            card.paste(inset, (cx - diameter // 2, cy - diameter // 2), inset)
        except Exception:  # noqa: BLE001 — any decode issue → fall back to glyph
            _draw_paw(draw, cx, cy, diameter, bg)
    else:
        _draw_paw(draw, cx, cy, diameter, bg)

    # Sparkle accents
    _draw_sparkle(draw, int(size * 0.78), int(size * 0.16), int(size * 0.04), "#FFD700")
    _draw_sparkle(draw, int(size * 0.2), int(size * 0.66), int(size * 0.028), "#FFFFFF")

    # Caption: the pose prompt, wrapped, on a darker pill near the bottom.
    font = _load_font(int(size * 0.052))
    wrapped = textwrap.fill(pose_prompt, width=26)
    bbox = draw.multiline_textbbox((0, 0), wrapped, font=font, spacing=4)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    pad = int(size * 0.04)
    pill_top = int(size * 0.74)
    draw.rounded_rectangle(
        (pad, pill_top, size - pad, pill_top + th + pad * 2),
        radius=int(size * 0.05),
        fill=INK if text_color == "#FFFFFF" else "#FFFFFF",
    )
    cap_color = "#FFFFFF" if text_color == "#FFFFFF" else INK
    draw.multiline_text(
        (size // 2, pill_top + pad),
        wrapped,
        font=font,
        fill=cap_color,
        anchor="ma",
        align="center",
        spacing=4,
    )

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    card.convert("RGB").save(out_path, "PNG")
    return out_path


def _draw_paw(draw: ImageDraw.ImageDraw, cx: int, cy: int, d: int, bg: str) -> None:
    """Fallback chunky paw glyph when no usable pet photo is available."""
    pad = d // 6
    draw.ellipse((cx - d // 4, cy - pad, cx + d // 4, cy + d // 3), fill=bg)
    for dx in (-d // 3, -d // 9, d // 9, d // 3):
        draw.ellipse(
            (cx + dx - d // 12, cy - d // 3, cx + dx + d // 12, cy - d // 12),
            fill=bg,
        )
