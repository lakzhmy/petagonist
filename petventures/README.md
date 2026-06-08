# Petventures 🐾

Turn your pet into a Tintin-style adventurer and send them strolling through a
real city — the result is an illustrated comic strip. A MACAD thesis project.

> **Status:** the demo focuses on the single **Petventures** experience
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
petventures/
├── frontend/   # React app (design system, flow, components)
└── backend/    # FastAPI (pet upload, stubbed variant generation, static media)
```

## What works today

The full Petventures flow runs end-to-end (all generation stubbed):

- **Step 1 — Your Pet:** give a photo, a description, or both (either is enough)
  → backend saves it → 8–12 character variants are generated (stubbed: the pet
  posterized into bold, palette-colored comic cards; description-only falls back
  to a paw glyph) → pick 1–5 favourites.
- **Step 2 — The Route:** a token-free vector map (OpenFreeMap) centered on
  Barcelona. Click to drop up to **8** numbered waypoints (auto-classified by
  place type — park / water / street …), reorder by drag, or **search a place /
  paste coordinates** to add a stop and fly there. Route line + fit-to-bounds.
- **Step 3 — The Comic:** generates panels where **each panel is themed by its
  stop's type** (a park panel has trees + birds, a waterside panel has the sea,
  etc.) and the pet is composited in. Panels land in a **3-column grid**; unused
  slots (fewer than 8 stops) become editable colour cells you can caption. Pick
  a layout **at download**: a printable 16:9 **Strip** (2×4 upright grid on
  yellow bands) or **Zine** (8-page fold-up booklet imposition — top row prints
  upside-down on purpose), as **PDF or PNG**.

Navigation is non-linear — the stepper, a **← Back** link, and **← Different
pet** let you move around without reloading.

Everything image-generation-related is stubbed with on-brand Pillow placeholders;
swap the `ComfyUIClient` / `streetview` bodies for the real pipeline later. See
the integration seams in `services/comfyui_client.py` (variant generation,
scene tintinify, composite) and `services/streetview.py` (Google Street View).

## Environment

Copy `.env.example` in each app if you want to override defaults
(map style URL on the frontend; Street View / ComfyUI keys on the backend —
both stubbed for now).
