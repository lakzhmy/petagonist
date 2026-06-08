"""Pet upload + character-variant generation endpoints."""

from __future__ import annotations

import os
import random
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from data.pose_prompts import POSE_PROMPTS
from models.schemas import (
    GenerateVariantsResponse,
    PetUploadResponse,
    Variant,
)
from services.comfyui_client import ComfyUIClient

router = APIRouter(prefix="/api/pet", tags=["pet"])

# Resolve paths relative to the backend root (this file is backend/routers/).
BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BACKEND_ROOT, "static", "uploads")
GENERATED_DIR = os.path.join(BACKEND_ROOT, "static", "generated")

comfy = ComfyUIClient(generated_root=GENERATED_DIR)

# In-memory pet store (single-process demo). Maps pet_id -> {image_path, ...}.
# A real deployment would persist this; for the thesis demo it lives in RAM.
PETS: dict[str, dict] = {}

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}


@router.post("/upload", response_model=PetUploadResponse)
async def upload_pet(
    image: UploadFile | None = File(None),
    description: str = Form(""),
) -> PetUploadResponse:
    """Accept a pet photo and/or description, save it, return an id.

    Either input is enough: a photo, a description, or both. Photo-only or
    photo+description give the best likeness (IP-Adapter has something to work
    from); description-only still works — the placeholder/real pipeline falls
    back to a text-driven pose with no photo to anchor the pet's look.
    """
    description = description.strip()
    has_image = image is not None and (image.filename or "") != ""
    if not has_image and not description:
        raise HTTPException(
            status_code=400,
            detail="Add a photo or a description of your pet (or both).",
        )

    pet_id = uuid.uuid4().hex[:12]
    save_path: str | None = None
    image_url: str | None = None

    if has_image:
        if image.content_type not in ALLOWED_TYPES:
            raise HTTPException(
                status_code=415,
                detail="Please upload a JPG, PNG, or WebP image of your pet.",
            )
        ext = EXT_BY_TYPE.get(image.content_type, ".png")
        os.makedirs(UPLOAD_DIR, exist_ok=True)
        save_path = os.path.join(UPLOAD_DIR, f"{pet_id}{ext}")
        data = await image.read()
        if not data:
            raise HTTPException(status_code=400, detail="That file looked empty.")
        with open(save_path, "wb") as f:
            f.write(data)
        image_url = f"/static/uploads/{pet_id}{ext}"

    PETS[pet_id] = {
        "image_path": save_path,  # None when description-only
        "image_url": image_url,
        "description": description,
    }
    return PetUploadResponse(pet_id=pet_id, image_url=image_url, description=description)


@router.post("/{pet_id}/generate-variants", response_model=GenerateVariantsResponse)
async def generate_variants(pet_id: str) -> GenerateVariantsResponse:
    """Generate 8–12 Tintin-style character variants for the uploaded pet.

    Stubbed: returns on-brand placeholder cards (see ComfyUIClient). The real
    pipeline will run a LoRA workflow per pose.
    """
    pet = PETS.get(pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Unknown pet — upload first.")

    # Randomly sample 8–12 distinct poses from the bank of 30.
    count = random.randint(8, 12)
    poses = random.sample(POSE_PROMPTS, count)

    variants = comfy.generate_pet_variants(
        image_path=pet["image_path"],
        description=pet["description"],
        pose_prompts=poses,
        pet_id=pet_id,
    )
    # Keep full variant details (incl. disk path + pose) for the comic step.
    pet["variants"] = {v["id"]: v for v in variants}

    return GenerateVariantsResponse(
        pet_id=pet_id,
        variants=[Variant(id=v["id"], image_url=v["image_url"], pose_prompt=v["pose_prompt"]) for v in variants],
    )
