"""Street View fetching — STUBBED with themed scene generation.

The real implementation will call the Google Street View Static API. For now we
draw a bold, flat "ligne claire"-ish scene whose look depends on the waypoint's
place type (park / water / street / plaza / building) — so panels feel varied
and connected to the route the user actually drew.
"""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

from .placeholders import _load_font

# STREETVIEW_API_KEY = os.environ.get("STREETVIEW_API_KEY")  # used by real impl

SKY = "#BFE8FF"
SKY_LOW = "#EAF7FF"


def _vgrad(img: Image.Image, box, top, bottom) -> None:
    x0, y0, x1, y1 = box
    h = max(1, y1 - y0)
    tr, tg, tb = Image.new("RGB", (1, 1), top).getpixel((0, 0))
    br, bg, bb = Image.new("RGB", (1, 1), bottom).getpixel((0, 0))
    d = ImageDraw.Draw(img)
    for i in range(h):
        t = i / h
        c = (int(tr + (br - tr) * t), int(tg + (bg - tg) * t), int(tb + (bb - tb) * t))
        d.line([(x0, y0 + i), (x1, y0 + i)], fill=c)


def _bird(d: ImageDraw.ImageDraw, x: int, y: int, s: int, color="#1A1A2E") -> None:
    d.arc((x - s, y - s, x, y + s), 200, 340, fill=color, width=3)
    d.arc((x, y - s, x + s, y + s), 200, 340, fill=color, width=3)


def _scene_park(img, w, h):
    _vgrad(img, (0, 0, w, int(h * 0.6)), SKY, SKY_LOW)
    d = ImageDraw.Draw(img)
    d.rectangle((0, int(h * 0.6), w, h), fill="#7ED957")
    d.rectangle((0, int(h * 0.78), w, h), fill="#5FB73F")
    # path
    d.polygon([(w * 0.42, h), (w * 0.58, h), (w * 0.54, h * 0.6), (w * 0.46, h * 0.6)], fill="#E9DFC8")
    # trees
    for tx, ty, r in [(0.16, 0.62, 0.13), (0.82, 0.6, 0.16), (0.3, 0.58, 0.1)]:
        cx, cy, rr = w * tx, h * ty, w * r
        d.rectangle((cx - rr * 0.12, cy, cx + rr * 0.12, cy + rr * 0.9), fill="#7A4A2B")
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr * 0.6), fill="#2E9E4F")
    for bx, by in [(0.5, 0.18), (0.58, 0.22), (0.66, 0.16)]:
        _bird(d, int(w * bx), int(h * by), 12)


def _scene_water(img, w, h):
    _vgrad(img, (0, 0, w, int(h * 0.5)), SKY, SKY_LOW)
    d = ImageDraw.Draw(img)
    _vgrad(img, (0, int(h * 0.5), w, h), "#3FA9F5", "#1E6FB8")
    d.line([(0, h * 0.5), (w, h * 0.5)], fill="#1E6FB8", width=3)
    for i in range(6):
        y = int(h * (0.58 + i * 0.06))
        for x in range(0, w, 60):
            off = (i % 2) * 30
            d.line([(x + off, y), (x + off + 22, y)], fill="#BFE8FF", width=3)
    # little sailboat
    bx, by = int(w * 0.7), int(h * 0.5)
    d.polygon([(bx, by), (bx + 46, by), (bx + 34, by + 18), (bx + 8, by + 18)], fill="#F5F0EB")
    d.polygon([(bx + 22, by - 40), (bx + 22, by - 2), (bx + 48, by - 2)], fill="#FF5C35")
    for bxx, byy in [(0.2, 0.16), (0.28, 0.2)]:
        _bird(d, int(w * bxx), int(h * byy), 11)


def _scene_buildings(img, w, h, road=True):
    _vgrad(img, (0, 0, w, h), SKY, SKY_LOW)
    d = ImageDraw.Draw(img)
    colors = ["#FFB37A", "#F58CB0", "#9C8CF5", "#7ED957", "#FFD700", "#5EC5FF"]
    x = 0
    i = 0
    base = int(h * (0.82 if road else 0.95))
    while x < w:
        bw = int(w * (0.1 + 0.05 * (i % 3)))
        bh = int(h * (0.32 + 0.12 * ((i * 3) % 4)))
        top = base - bh
        d.rectangle((x, top, x + bw - 6, base), fill=colors[i % len(colors)], outline="#1A1A2E", width=2)
        for wy in range(top + 14, base - 14, 26):
            for wx in range(x + 12, x + bw - 18, 24):
                d.rectangle((wx, wy, wx + 12, wy + 14), fill="#1A1A2E")
        x += bw
        i += 1
    if road:
        d.rectangle((0, base, w, h), fill="#5A5A66")
        for rx in range(0, w, 70):
            d.rectangle((rx, int((base + h) / 2) - 3, rx + 34, int((base + h) / 2) + 3), fill="#FFD700")


def _scene_plaza(img, w, h):
    _vgrad(img, (0, 0, w, int(h * 0.55)), SKY, SKY_LOW)
    d = ImageDraw.Draw(img)
    # distant low buildings
    colors = ["#FFB37A", "#F58CB0", "#9C8CF5", "#7ED957"]
    x, i = 0, 0
    while x < w:
        bw = int(w * 0.16)
        bh = int(h * 0.18)
        d.rectangle((x, int(h * 0.55) - bh, x + bw - 6, int(h * 0.55)), fill=colors[i % 4], outline="#1A1A2E", width=2)
        x += bw
        i += 1
    # paved ground
    d.rectangle((0, int(h * 0.55), w, h), fill="#E9DFC8")
    for gy in range(int(h * 0.6), h, 28):
        d.line([(0, gy), (w, gy)], fill="#D2C6A6", width=2)
    for gx in range(0, w, 60):
        d.line([(gx, int(h * 0.55)), (gx, h)], fill="#D2C6A6", width=2)
    # pigeons on the ground
    for px, py in [(0.3, 0.8), (0.4, 0.85), (0.62, 0.78), (0.7, 0.86)]:
        cx, cy = int(w * px), int(h * py)
        d.ellipse((cx - 10, cy - 7, cx + 10, cy + 7), fill="#7A7A88")
        d.ellipse((cx + 6, cy - 12, cx + 16, cy - 2), fill="#7A7A88")


SCENES = {
    "park": _scene_park,
    "water": _scene_water,
    "plaza": _scene_plaza,
    "building": lambda img, w, h: _scene_buildings(img, w, h, road=False),
    "street": lambda img, w, h: _scene_buildings(img, w, h, road=True),
    "place": lambda img, w, h: _scene_buildings(img, w, h, road=True),
}


def fetch_street_view(
    lat: float,
    lng: float,
    place_type: str = "place",
    location_name: str | None = None,
    out_path: str = "scene.png",
    size: tuple[int, int] = (900, 600),
) -> str:
    """Return a path to a scene image for the given coordinates.

    Real implementation (commented) would fetch the actual panorama:

        # url = (
        #     "https://maps.googleapis.com/maps/api/streetview"
        #     f"?size={size[0]}x{size[1]}&location={lat},{lng}"
        #     f"&key={STREETVIEW_API_KEY}"
        # )
        # img_bytes = requests.get(url).content
    """
    w, h = size
    img = Image.new("RGB", (w, h), SKY)
    SCENES.get(place_type, SCENES["place"])(img, w, h)

    # Small location tag in the corner.
    d = ImageDraw.Draw(img)
    label = location_name or f"{lat:.4f}, {lng:.4f}"
    font = _load_font(20)
    tb = d.textbbox((0, 0), label, font=font)
    tw = tb[2] - tb[0]
    d.rounded_rectangle((14, 14, 14 + tw + 24, 50), radius=14, fill="#1A1A2E")
    d.text((26, 22), label, font=font, fill="#FFFFFF")

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
