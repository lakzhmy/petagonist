"""Comic-strip layout: combine panels into a downloadable strip PNG + PDF.

`build_print_template` produces the two printable 16:9 pages the UI offers at
download time: a **strip** (2×4 upright grid on yellow bands) and a fold-up
**zine** (8-page booklet imposition — the top row is rotated 180°). Both always
have 8 cells; with fewer panels the extras render as solid colour blocks with an
optional caption.
"""

from __future__ import annotations

import os
import textwrap

from PIL import Image, ImageDraw, ImageOps

from .placeholders import _load_font

GAP = 18
PAD = 24
BG = "#4A2FBD"  # grape

# ---- Print template constants ---------------------------------------------
PAGE = (1920, 1080)  # 16:9
PINK = "#FBD0DA"  # page background
SUN = "#FFD93B"  # strip row band
GUIDE = "#B98AA8"  # zine dashed cut/fold guides
# Brand colours cycled for blank cells (slots beyond the panel count).
BLANK_COLORS = ["#FF5C35", "#4A2FBD", "#FF69B4", "#7ED957", "#5EC5FF", "#FFD700", "#9C8CF5", "#FF8FAB"]


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


# ===========================================================================
# Printable 16:9 templates (strip / zine)
# ===========================================================================

CORNER = 28


def _rounded(img: Image.Image, radius: int = CORNER) -> Image.Image:
    """Return an RGBA copy of `img` with rounded corners (transparent outside)."""
    rgba = img.convert("RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, img.size[0] - 1, img.size[1] - 1), radius=radius, fill=255
    )
    rgba.putalpha(mask)
    return rgba


def _panel_cell(panel: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Letterbox a comic panel into a white, rounded cell of `size`."""
    cell = Image.new("RGB", size, "#FFFFFF")
    fitted = ImageOps.contain(panel.convert("RGB"), size, Image.LANCZOS)
    cell.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return _rounded(cell)


def _blank_cell(size: tuple[int, int], color: str, caption: str) -> Image.Image:
    """A solid-colour rounded cell with an optional centered caption."""
    cell = Image.new("RGB", size, color)
    if caption.strip():
        d = ImageDraw.Draw(cell)
        font = _load_font(40)
        wrapped = textwrap.fill(caption.strip(), width=16)
        d.multiline_text(
            (size[0] // 2, size[1] // 2),
            wrapped,
            font=font,
            fill="#FFFFFF",
            anchor="mm",
            align="center",
            spacing=8,
        )
    return _rounded(cell)


def _dashed_line(d: ImageDraw.ImageDraw, p0, p1, color=GUIDE, width=3, dash=20, gap=14) -> None:
    """Draw a dashed horizontal or vertical line from p0 to p1."""
    x0, y0 = p0
    x1, y1 = p1
    if y0 == y1:  # horizontal
        x = x0
        while x < x1:
            d.line([(x, y0), (min(x + dash, x1), y0)], fill=color, width=width)
            x += dash + gap
    else:  # vertical
        y = y0
        while y < y1:
            d.line([(x0, y), (x0, min(y + dash, y1))], fill=color, width=width)
            y += dash + gap


def build_print_template(
    panel_paths: list[str],
    captions: dict[str, str],
    template: str,
    out_path: str,
    fmt: str = "pdf",
) -> str:
    """Render a printable 16:9 page (strip or zine) and save as PDF or PNG.

    Always lays out 8 cells. Slot i (0-based) shows panel i if it exists, else a
    blank colour block carrying captions.get(str(i)). For the zine the top row is
    rotated 180° and the page order is the classic 8-page booklet imposition.
    """
    W, H = PAGE
    margin, gap = 70, 28
    cols, rows = 4, 2
    cw = (W - 2 * margin - (cols - 1) * gap) // cols
    ch = (H - 2 * margin - (rows - 1) * gap) // rows

    panels = [Image.open(p) for p in panel_paths[:8]]
    n = len(panels)

    def slot_cell(i: int) -> Image.Image:
        if i < n:
            return _panel_cell(panels[i], (cw, ch))
        return _blank_cell((cw, ch), BLANK_COLORS[i % len(BLANK_COLORS)], captions.get(str(i), ""))

    def xy(col: int, row: int) -> tuple[int, int]:
        return margin + col * (cw + gap), margin + row * (ch + gap)

    page = Image.new("RGB", (W, H), PINK)
    pd = ImageDraw.Draw(page)

    if template == "zine":
        # 8-page fold-up imposition. Bottom row upright; top row upside down.
        #   bottom L→R:  BACK(img8)  FRONT(img1)  img2  img3   -> slots 7,0,1,2
        #   top L→R (180°): img7  img6  img5  img4            -> slots 6,5,4,3
        top = [6, 5, 4, 3]
        bottom = [7, 0, 1, 2]
        for col, idx in enumerate(top):
            cell = slot_cell(idx).rotate(180)
            page.paste(cell, xy(col, 0), cell)
        for col, idx in enumerate(bottom):
            cell = slot_cell(idx)
            page.paste(cell, xy(col, 1), cell)
        # Dashed cut/fold guides: 3 vertical, 1 horizontal, + outer border.
        for col in range(1, cols):
            gx = margin + col * (cw + gap) - gap // 2
            _dashed_line(pd, (gx, margin), (gx, H - margin))
        gy = margin + ch + gap // 2
        _dashed_line(pd, (margin, gy), (W - margin, gy))
        _dashed_line(pd, (margin, margin), (W - margin, margin))
        _dashed_line(pd, (margin, H - margin), (W - margin, H - margin))
        _dashed_line(pd, (margin, margin), (margin, H - margin))
        _dashed_line(pd, (W - margin, margin), (W - margin, H - margin))
    else:  # strip — upright 2×4 reading order on yellow row bands
        for row in range(rows):
            x0, y0 = margin - 18, margin + row * (ch + gap) - 18
            pd.rounded_rectangle((x0, y0, W - margin + 18, y0 + ch + 36), radius=40, fill=SUN)
        for k in range(8):
            col, row = k % cols, k // cols
            cell = slot_cell(k)
            page.paste(cell, xy(col, row), cell)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if fmt == "png":
        page.save(out_path, "PNG")
    else:
        page.save(out_path, "PDF", resolution=150)
    return out_path
