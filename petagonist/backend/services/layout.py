"""Comic-strip layout: combine panels into a downloadable strip PNG + PDF.

`build_print_template` produces the two printable pages the UI offers at
download time: a **strip** (2×4 reading-order grid) and a fold-up **zine**
(8-page booklet imposition — the top row is rotated 180°). Both always have
8 cells; with fewer panels the extras render as solid colour blocks with an
optional caption. Each cell sits inside a coloured frame with rounded inner
edges — the frame colours double as cut/fold guides (no dashed lines).

Page: 17×11 inches (tabloid) at 150 DPI = 2550×1650 px.
Frame area: 16×8 inches centered = 2400×1200 px → 4×2 grid of 600×600 cells.
"""

from __future__ import annotations

import os
import textwrap

from PIL import Image, ImageDraw, ImageOps

from .placeholders import _load_font

GAP = 18
PAD = 24
BG = "#4A2FBD"  # grape

# ---- Print template constants -----------------------------------------------

DPI = 150
PAGE = (int(17 * DPI), int(11 * DPI))  # 2550 × 1650
FRAME_W, FRAME_H = int(16 * DPI), int(8 * DPI)  # 2400 × 1200
COLS, ROWS = 4, 2
CELL = FRAME_W // COLS  # 600 × 600

FRAME_BORDER = 34  # px of coloured frame around each panel
INNER = CELL - 2 * FRAME_BORDER  # 532 px inner panel area
CORNER = 64  # rounded corner radius on the inner cutout

# Frame colours by grid position (from the Illustrator SVG).
# Each row is L→R; [row][col].
FRAME_COLORS = [
    ["#f15d3c", "#50479d", "#f06ba8", "#87c65a"],  # row 0
    ["#fdd700", "#6cc1ec", "#f15d3c", "#50479d"],  # row 1
]

# Brand colours cycled for blank cells (slots beyond the panel count).
BLANK_COLORS = [
    "#FF5C35", "#4A2FBD", "#FF69B4", "#7ED957",
    "#5EC5FF", "#FFD700", "#9C8CF5", "#FF8FAB",
]


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
    panels[0].save(out_path, "PDF", save_all=True, append_images=panels[1:], resolution=DPI)
    return out_path


# ===========================================================================
# Printable templates (strip / zine) with coloured frames
# ===========================================================================

def _rounded_mask(size: tuple[int, int], radius: int) -> Image.Image:
    """Create an L-mode mask with a white rounded rectangle."""
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, size[0] - 1, size[1] - 1), radius=radius, fill=255,
    )
    return mask


def _fit_square(panel: Image.Image, size: int) -> Image.Image:
    """Crop-to-fill a panel into a square, then resize."""
    return ImageOps.fit(panel.convert("RGB"), (size, size), Image.LANCZOS)


def _framed_cell(
    panel: Image.Image | None,
    frame_color: str,
    blank_color: str = "",
    caption: str = "",
) -> Image.Image:
    """Build one 600×600 cell: coloured frame with a rounded-corner panel inside."""
    cell = Image.new("RGB", (CELL, CELL), frame_color)

    if panel is not None:
        inner = _fit_square(panel, INNER)
    else:
        inner = Image.new("RGB", (INNER, INNER), blank_color or frame_color)
        if caption.strip():
            d = ImageDraw.Draw(inner)
            font = _load_font(36)
            wrapped = textwrap.fill(caption.strip(), width=14)
            d.multiline_text(
                (INNER // 2, INNER // 2),
                wrapped,
                font=font,
                fill="#FFFFFF",
                anchor="mm",
                align="center",
                spacing=8,
            )

    mask = _rounded_mask((INNER, INNER), CORNER)
    cell.paste(inner, (FRAME_BORDER, FRAME_BORDER), mask)
    return cell


def build_print_template(
    panel_paths: list[str],
    captions: dict[str, str],
    template: str,
    out_path: str,
    fmt: str = "pdf",
) -> str:
    """Render a printable tabloid page (strip or zine) and save as PDF or PNG.

    Always lays out 8 cells. Slot i (0-based) shows panel i if it exists,
    else a blank colour block carrying captions.get(str(i)). For the zine the
    top row is rotated 180° and the page order is the classic 8-page booklet
    imposition. Coloured frames replace dashed cut/fold guides.
    """
    W, H = PAGE
    mx = (W - FRAME_W) // 2  # horizontal margin (75 px)
    my = (H - FRAME_H) // 2  # vertical margin (225 px)

    panels = [Image.open(p) for p in panel_paths[:8]]
    n = len(panels)

    def slot_cell(slot: int, col: int, row: int) -> Image.Image:
        color = FRAME_COLORS[row][col]
        if slot < n:
            return _framed_cell(panels[slot], color)
        blank = BLANK_COLORS[slot % len(BLANK_COLORS)]
        return _framed_cell(None, color, blank_color=blank, caption=captions.get(str(slot), ""))

    page = Image.new("RGB", (W, H), "#FFFFFF")

    if template == "zine":
        top_slots = [6, 5, 4, 3]
        bottom_slots = [7, 0, 1, 2]
        for col, slot in enumerate(top_slots):
            cell = slot_cell(slot, col, 0).rotate(180)
            page.paste(cell, (mx + col * CELL, my))
        for col, slot in enumerate(bottom_slots):
            cell = slot_cell(slot, col, 1)
            page.paste(cell, (mx + col * CELL, my + CELL))
    else:
        for k in range(8):
            col, row = k % COLS, k // COLS
            cell = slot_cell(k, col, row)
            page.paste(cell, (mx + col * CELL, my + row * CELL))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    if fmt == "png":
        page.save(out_path, "PNG")
    else:
        page.save(out_path, "PDF", resolution=DPI)
    return out_path
