"""Scene source for the comic pipeline.

`fetch_street_view` is the one function the pipeline calls to get a scene image
for a coordinate. It now tries **Mapillary** first (real street-level photo near
the point), and falls back to a drawn, themed placeholder when there's no token,
no coverage, or any error — so the app always produces a panel.

`seed` is the re-roll counter: for Mapillary it selects candidate #seed from the
ranked results (so ↻ cycles real photos); for the placeholder it varies the
drawn scene. The photo gets a light comic treatment to bridge the look until the
ComfyUI tintinify pass exists.
"""

from __future__ import annotations

import io
import json
import math
import os
import random
import urllib.parse
import urllib.request

from PIL import Image, ImageDraw, ImageEnhance, ImageOps

MAPILLARY_GRAPH = "https://graph.mapillary.com/images"
# Progressively widen the search until we find coverage near the point.
SEARCH_RADII_M = (60, 150, 350)


def _mapillary_token() -> str | None:
    return os.environ.get("MAPILLARY_TOKEN") or os.environ.get("MapillaryToken")


def _bbox(lat: float, lng: float, meters: float = 60.0) -> str:
    """A small bounding box (min_lon,min_lat,max_lon,max_lat) around the point."""
    dlat = meters / 111_320.0
    dlng = meters / (111_320.0 * max(0.01, math.cos(math.radians(lat))))
    return f"{lng - dlng:.6f},{lat - dlat:.6f},{lng + dlng:.6f},{lat + dlat:.6f}"


def _mapillary_scene(lat, lng, seed, location_name, out_path, size, token) -> str | None:
    """Fetch a real Mapillary photo near (lat,lng); return out_path or None.

    Ranks candidates (flat over pano, then nearest, then most recent) and picks
    #seed so re-rolling cycles through the real coverage at that spot.
    """
    fields = "id,computed_geometry,geometry,compass_angle,captured_at,thumb_1024_url,is_pano"
    # access_token kept literal (it contains | which must not be percent-encoded).
    data = []
    for meters in SEARCH_RADII_M:
        qs = urllib.parse.urlencode({"fields": fields, "bbox": _bbox(lat, lng, meters), "limit": 40})
        url = f"{MAPILLARY_GRAPH}?access_token={token}&{qs}"
        req = urllib.request.Request(url, headers={"User-Agent": "petventures/0.1"})
        with urllib.request.urlopen(req, timeout=15) as r:
            data = (json.load(r) or {}).get("data", [])
        if data:
            break
    if not data:
        return None

    def dist(c):
        g = c.get("computed_geometry") or c.get("geometry") or {}
        co = g.get("coordinates")
        return ((co[1] - lat) ** 2 + (co[0] - lng) ** 2) if co else 9e9

    ranked = sorted(data, key=lambda c: (1 if c.get("is_pano") else 0, dist(c), -(c.get("captured_at") or 0)))
    chosen = ranked[seed % len(ranked)]
    thumb = chosen.get("thumb_1024_url")
    if not thumb:
        return None

    ireq = urllib.request.Request(thumb, headers={"User-Agent": "petventures/0.1"})
    with urllib.request.urlopen(ireq, timeout=20) as r:
        photo = Image.open(io.BytesIO(r.read())).convert("RGB")

    photo = ImageOps.fit(photo, size, Image.LANCZOS)
    # Light comic treatment so the photo blends until ComfyUI tintinify lands.
    photo = ImageEnhance.Color(photo).enhance(1.25)
    photo = ImageEnhance.Contrast(photo).enhance(1.08)
    photo = ImageOps.posterize(photo, 5)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    photo.save(out_path, "PNG")
    return out_path

# A small set of sky palettes; the seed picks one, so re-rolls read as different
# times of day — the cheapest "this is a different photo" signal.
SKIES = [
    ("#BFE8FF", "#EAF7FF"),  # clear day
    ("#FFD8A8", "#FFF3E0"),  # golden hour
    ("#A8C8FF", "#DCE8FF"),  # cool midday
    ("#FFC2D1", "#FFE8EF"),  # pink dusk
]


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


def _scene_park(img, w, h, rng, sky):
    _vgrad(img, (0, 0, w, int(h * 0.6)), sky[0], sky[1])
    d = ImageDraw.Draw(img)
    d.rectangle((0, int(h * 0.6), w, h), fill="#7ED957")
    d.rectangle((0, int(h * 0.78), w, h), fill="#5FB73F")
    # path
    d.polygon([(w * 0.42, h), (w * 0.58, h), (w * 0.54, h * 0.6), (w * 0.46, h * 0.6)], fill="#E9DFC8")
    # trees — jittered count + positions
    n = rng.randint(3, 4)
    for _ in range(n):
        tx = rng.uniform(0.08, 0.9)
        ty = rng.uniform(0.56, 0.64)
        r = rng.uniform(0.1, 0.16)
        cx, cy, rr = w * tx, h * ty, w * r
        d.rectangle((cx - rr * 0.12, cy, cx + rr * 0.12, cy + rr * 0.9), fill="#7A4A2B")
        d.ellipse((cx - rr, cy - rr, cx + rr, cy + rr * 0.6), fill="#2E9E4F")
    for _ in range(rng.randint(2, 4)):
        _bird(d, int(w * rng.uniform(0.45, 0.7)), int(h * rng.uniform(0.14, 0.26)), 12)


def _scene_water(img, w, h, rng, sky):
    _vgrad(img, (0, 0, w, int(h * 0.5)), sky[0], sky[1])
    d = ImageDraw.Draw(img)
    _vgrad(img, (0, int(h * 0.5), w, h), "#3FA9F5", "#1E6FB8")
    d.line([(0, h * 0.5), (w, h * 0.5)], fill="#1E6FB8", width=3)
    for i in range(6):
        y = int(h * (0.58 + i * 0.06))
        for x in range(0, w, 60):
            off = (i % 2) * 30
            d.line([(x + off, y), (x + off + 22, y)], fill="#BFE8FF", width=3)
    # little sailboat at a jittered position
    bx, by = int(w * rng.uniform(0.5, 0.8)), int(h * 0.5)
    d.polygon([(bx, by), (bx + 46, by), (bx + 34, by + 18), (bx + 8, by + 18)], fill="#F5F0EB")
    d.polygon([(bx + 22, by - 40), (bx + 22, by - 2), (bx + 48, by - 2)], fill="#FF5C35")
    for _ in range(rng.randint(2, 3)):
        _bird(d, int(w * rng.uniform(0.15, 0.4)), int(h * rng.uniform(0.14, 0.24)), 11)


def _scene_buildings(img, w, h, rng, sky, road=True):
    _vgrad(img, (0, 0, w, h), sky[0], sky[1])
    d = ImageDraw.Draw(img)
    colors = ["#FFB37A", "#F58CB0", "#9C8CF5", "#7ED957", "#FFD700", "#5EC5FF"]
    rng.shuffle(colors)
    x = 0
    i = 0
    base = int(h * (0.82 if road else 0.95))
    while x < w:
        bw = int(w * (0.1 + 0.05 * (i % 3)))
        bh = int(h * (0.3 + 0.16 * rng.random()))
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


def _scene_plaza(img, w, h, rng, sky):
    _vgrad(img, (0, 0, w, int(h * 0.55)), sky[0], sky[1])
    d = ImageDraw.Draw(img)
    # distant low buildings
    colors = ["#FFB37A", "#F58CB0", "#9C8CF5", "#7ED957"]
    rng.shuffle(colors)
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
    # pigeons on the ground at jittered spots
    for _ in range(rng.randint(3, 5)):
        cx, cy = int(w * rng.uniform(0.25, 0.75)), int(h * rng.uniform(0.74, 0.88))
        d.ellipse((cx - 10, cy - 7, cx + 10, cy + 7), fill="#7A7A88")
        d.ellipse((cx + 6, cy - 12, cx + 16, cy - 2), fill="#7A7A88")


SCENES = {
    "park": _scene_park,
    "water": _scene_water,
    "plaza": _scene_plaza,
    "building": lambda img, w, h, rng, sky: _scene_buildings(img, w, h, rng, sky, road=False),
    "street": lambda img, w, h, rng, sky: _scene_buildings(img, w, h, rng, sky, road=True),
    "place": lambda img, w, h, rng, sky: _scene_buildings(img, w, h, rng, sky, road=True),
}


def fetch_street_view(
    lat: float,
    lng: float,
    place_type: str = "place",
    location_name: str | None = None,
    out_path: str = "scene.png",
    size: tuple[int, int] = (900, 600),
    seed: int = 0,
) -> str:
    """Return a path to a scene image for the given coordinates.

    Tries Mapillary first (real street-level photo near the point, candidate
    #seed); on no token / no coverage / any error, draws a seeded themed
    placeholder so a panel is always produced.
    """
    # 1) Real street-level photo via Mapillary (if configured + covered).
    token = _mapillary_token()
    if token:
        try:
            path = _mapillary_scene(lat, lng, seed, location_name, out_path, size, token)
            if path:
                return path
        except Exception:  # noqa: BLE001 — network/parse issues fall back to drawn scene
            pass

    # 2) Drawn placeholder, varied by seed.
    rng = random.Random(seed)
    sky = rng.choice(SKIES)
    w, h = size
    img = Image.new("RGB", (w, h), sky[0])
    SCENES.get(place_type, SCENES["place"])(img, w, h, rng, sky)

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    img.save(out_path, "PNG")
    return out_path
