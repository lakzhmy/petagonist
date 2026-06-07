"""Pydantic request/response models shared across routers."""

from pydantic import BaseModel, Field


# ---- Pet upload -----------------------------------------------------------


class PetUploadResponse(BaseModel):
    pet_id: str
    image_url: str
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


class GenerateComicRequest(BaseModel):
    pet_id: str
    selected_variant_ids: list[str] = Field(default_factory=list)
    waypoints: list[Waypoint] = Field(default_factory=list)


class Panel(BaseModel):
    order: int
    image_url: str
    location_name: str


class GenerateComicResponse(BaseModel):
    comic_id: str
    panels: list[Panel]
    strip_url: str | None = None
