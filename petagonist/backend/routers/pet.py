"""Pet upload + character-variant generation endpoints."""

from __future__ import annotations

import json
import os
import random
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from data.pose_prompts import POSE_PROMPTS
from models.schemas import (
    GenerateVariantsResponse,
    PetUploadResponse,
    Variant,
)
from services.comfyui_client import ComfyUIClient

router = APIRouter(prefix="/api/pet", tags=["pet"])

BACKEND_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_DIR = os.path.join(BACKEND_ROOT, "static", "uploads")
GENERATED_DIR = os.path.join(BACKEND_ROOT, "static", "generated")

comfy = ComfyUIClient(generated_root=GENERATED_DIR)

PETS: dict[str, dict] = {}

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
EXT_BY_TYPE = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}

VARIANT_COUNT = 6


@router.post("/upload", response_model=PetUploadResponse)
async def upload_pet(
    image: UploadFile | None = File(None),
    description: str = Form(""),
) -> PetUploadResponse:
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
        "image_path": save_path,
        "image_url": image_url,
        "description": description,
        "variants": {},
        "next_index": 0,
    }
    return PetUploadResponse(pet_id=pet_id, image_url=image_url, description=description)


@router.post("/{pet_id}/generate-variants", response_model=GenerateVariantsResponse)
async def generate_variants(pet_id: str) -> GenerateVariantsResponse:
    """Batch generate — kept for backwards compatibility."""
    pet = PETS.get(pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Unknown pet — upload first.")

    poses = random.sample(POSE_PROMPTS, VARIANT_COUNT)
    variants = comfy.generate_pet_variants(
        image_path=pet["image_path"],
        description=pet["description"],
        pose_prompts=poses,
        pet_id=pet_id,
    )
    pet["variants"] = {v["id"]: v for v in variants}
    pet["next_index"] = len(variants)

    return GenerateVariantsResponse(
        pet_id=pet_id,
        variants=[Variant(id=v["id"], image_url=v["image_url"], pose_prompt=v["pose_prompt"]) for v in variants],
    )


@router.post("/{pet_id}/generate-variants-stream")
async def generate_variants_stream(pet_id: str):
    """SSE endpoint — streams each variant as it finishes."""
    pet = PETS.get(pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Unknown pet — upload first.")

    poses = random.sample(POSE_PROMPTS, VARIANT_COUNT)
    comfy_filename = comfy.prepare_comfyui(pet["image_path"])

    def event_stream():
        total = len(poses)
        yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"

        for i, pose in enumerate(poses):
            idx = pet.get("next_index", 0) + i
            v = comfy.generate_single_variant(
                image_path=pet["image_path"],
                description=pet["description"],
                pose=pose,
                pet_id=pet_id,
                index=idx,
                comfy_filename=comfy_filename,
            )
            pet["variants"][v["id"]] = v
            variant_data = {
                "type": "variant",
                "index": i,
                "total": total,
                "variant": {"id": v["id"], "image_url": v["image_url"], "pose_prompt": v["pose_prompt"]},
            }
            yield f"data: {json.dumps(variant_data)}\n\n"

        pet["next_index"] = pet.get("next_index", 0) + total
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.post("/{pet_id}/regenerate-variant")
async def regenerate_variant(pet_id: str, old_variant_id: str = "", pose_prompt: str = ""):
    """Regenerate a single variant, optionally with a custom prompt."""
    pet = PETS.get(pet_id)
    if pet is None:
        raise HTTPException(status_code=404, detail="Unknown pet — upload first.")

    if not pose_prompt:
        pose_prompt = random.choice(POSE_PROMPTS)

    idx = pet.get("next_index", 0)
    pet["next_index"] = idx + 1

    comfy_filename = comfy.prepare_comfyui(pet["image_path"])
    v = comfy.generate_single_variant(
        image_path=pet["image_path"],
        description=pet["description"],
        pose=pose_prompt,
        pet_id=pet_id,
        index=idx,
        comfy_filename=comfy_filename,
    )

    if old_variant_id and old_variant_id in pet["variants"]:
        del pet["variants"][old_variant_id]
    pet["variants"][v["id"]] = v

    return {"variant": {"id": v["id"], "image_url": v["image_url"], "pose_prompt": v["pose_prompt"]}}
