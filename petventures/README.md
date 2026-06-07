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

- **Step 1 — Your Pet:** drag-drop a photo + description → backend saves it →
  8–12 character variants are generated (stubbed: the pet posterized into bold,
  palette-colored comic cards) → pick 1–5 favourites.
- **Steps 2–3 — Route & Comic:** placeholders, built in the next slices.

## Environment

Copy `.env.example` in each app if you want to override defaults
(map style URL on the frontend; Street View / ComfyUI keys on the backend —
both stubbed for now).
