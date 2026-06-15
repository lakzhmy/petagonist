"""Pydantic request/response models shared across routers."""

from pydantic import BaseModel, Field


# ---- Pet upload -----------------------------------------------------------


class PetUploadResponse(BaseModel):
    pet_id: str
    image_url: str | None = None  # None when the pet was described but not photographed
    description: str


# ---- Character variants ---------------------------------------------------


class Variant(BaseModel):
    id: str
    image_url: str
    pose_prompt: str


class GenerateVariantsResponse(BaseModel):
    pet_id: str
    variants: list[Variant]


# ---- Flâneur comic generation (wired up in a later slice) -----------------


class Waypoint(BaseModel):
    lat: float
    lng: float
    order: int
    type: str = "place"
    name: str | None = None
    scene_url: str | None = None


class GenerateComicRequest(BaseModel):
    pet_id: str
    selected_variant_ids: list[str] = Field(default_factory=list)
    waypoints: list[Waypoint] = Field(default_factory=list)


class Panel(BaseModel):
    order: int
    image_url: str
    location_name: str
    type: str = "place"


class GenerateComicResponse(BaseModel):
    comic_id: str
    panels: list[Panel]
    strip_url: str | None = None
    pdf_url: str | None = None


# ---- Print-template export (strip / zine) ---------------------------------


class ExportRequest(BaseModel):
    comic_id: str
    template: str = "strip"  # 'strip' | 'zine'
    format: str = "pdf"  # 'pdf' | 'png'
    # Captions for blank cells, keyed by slot index ("0".."7") as a string.
    captions: dict[str, str] = Field(default_factory=dict)


class ExportResponse(BaseModel):
    url: str


# ---- Per-panel regenerate (re-roll the scene for one stop) -----------------


class RegeneratePanelRequest(BaseModel):
    comic_id: str
    order: int
    mode: str = "all"  # "all" | "character" | "background"
