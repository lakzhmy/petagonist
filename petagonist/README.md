# Petagonist 🐾

Turn your pet into a Tintin-style adventurer and send them strolling through a
real city — the result is an illustrated comic strip. A MACAD thesis project.

> **Status:** the demo focuses on the single **Petagonist** experience
> (upload → pick characters → draw a route → comic). The I-SPY and IsoBuild
> modes are parked (hidden), and all heavy generation is **stubbed** with
> on-brand placeholders so everything runs without ComfyUI or API keys.

## Stack

- **Frontend:** React (Vite) + React Router + Tailwind v4
- **Backend:** FastAPI + Pillow (placeholder image generation)
- **Map:** MapLibre GL JS (token-free) — _wired in a later slice_

## Running it

Two processes. The Vite dev server proxies `/api` and `/static` to the backend,
so you only ever open **http://localhost:5173**.

### Backend (port 8000)

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows  (use: source .venv/bin/activate on macOS/Linux)
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend (port 5173)

```bash
cd frontend
npm install
npm run dev
```

Then open http://localhost:5173.

## Project layout

```
petagonist/
├── frontend/   # React app (design system, flow, components)
└── backend/    # FastAPI (pet upload, stubbed variant generation, static media)
```

## What works today

The full Petagonist flow runs end-to-end (all generation stubbed):

- **Step 1 — Your Pet:** give a photo, a description, or both (either is enough)
  → backend saves it → 8–12 character variants are generated (stubbed: the pet
  posterized into bold, palette-colored comic cards; description-only falls back
  to a paw glyph) → pick 1–5 favourites.
- **Step 2 — The Route:** a token-free vector map (OpenFreeMap) centered on
  Barcelona. Click to drop up to **8** numbered waypoints (auto-classified by
  place type — park / water / street …), reorder by drag, or **search a place /
  paste coordinates** to add a stop and fly there. Route line + fit-to-bounds.
  Toggle **photo coverage** to see which streets have Mapillary imagery before
  dropping pins (tiles proxied through the backend so the token stays server-side).
- **Step 3 — The Comic:** generates panels where **each panel is themed by its
  stop's type** (a park panel has trees + birds, a waterside panel has the sea,
  etc.) and the pet is composited in. Panels land in a **3-column grid**; unused
  slots (fewer than 8 stops) become editable colour cells you can caption. Each
  panel has a **↻ re-roll** that swaps in a different scene + pose for that stop —
  the next **Mapillary** photo of that spot when a token is set, else a re-seeded
  drawn placeholder.
  Pick a layout **at download**: a printable 16:9 **Strip** (2×4 upright grid on
  yellow bands) or **Zine** (8-page fold-up booklet imposition — top row prints
  upside-down on purpose), as **PDF or PNG**.

Navigation is non-linear — the stepper, a **← Back** link, and **← Different
pet** let you move around without reloading.

Scene backgrounds are **live via Mapillary** when a token is set; the AI styling
steps are still stubbed with on-brand Pillow placeholders. Each seam swaps out
independently — nothing else changes:

- `services/streetview.py` `fetch_street_view(lat, lng, type, …, seed)` — the
  **scene source**. With a Mapillary token it ranks images near the point
  (flat-over-pano → nearest → most recent) and returns candidate `#seed` (so ↻
  cycles real coverage), lightly comic-treated. No token / no coverage / any
  error → a seeded drawn placeholder. Set `MAPILLARY_TOKEN` (or `MapillaryToken`)
  in a `.env` at the repo root or `backend/`.
- `services/comfyui_client.py` — variant generation, scene **tintinify** (Tintin
  LoRA + ControlNet), and pet composite — still stubbed.

## Environment

Copy `.env.example` in each app to override defaults. Backend: `MAPILLARY_TOKEN`
enables real street-level scenes (free token; falls back to drawn scenes
without it); ComfyUI URL is stubbed. Frontend: optional map style URL.
The `.env` is git-ignored — keep your token out of commits.
