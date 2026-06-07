"""ComfyUI client — STUBBED.

Everything generation-related is stubbed so the app works end-to-end without a
ComfyUI instance running. Each method has the shape of its real counterpart and
a commented sketch of the actual API call. Swap the bodies later; the routers
won't need to change.
"""

from __future__ import annotations

import os
import uuid

from .placeholders import generate_variant_card

# Where the real ComfyUI server would live (env-overridable).
COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:8188")


class ComfyUIClient:
    """Thin wrapper around the (future) ComfyUI REST API."""

    def __init__(self, generated_root: str):
        # Directory under which generated images are written + served.
        self.generated_root = generated_root

    # -- Character variants -------------------------------------------------

    def generate_pet_variants(
        self, image_path: str | None, description: str, pose_prompts: list[str], pet_id: str
    ) -> list[dict]:
        """Generate Tintin-style character variants of the pet, one per pose.

        Real implementation will queue a LoRA + IP-Adapter workflow per pose and
        poll for the result:

            # workflow = build_variant_workflow(image_path, description, pose)
            # r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
            # prompt_id = r.json()["prompt_id"]
            # img = poll_until_done(prompt_id)

        Stub: render an on-brand placeholder card per pose (the pet posterized
        into a comic inset + the pose text), returning one dict per variant.
        """
        out_dir = os.path.join(self.generated_root, pet_id)
        variants: list[dict] = []
        for i, pose in enumerate(pose_prompts):
            variant_id = uuid.uuid4().hex[:8]
            filename = f"variant_{i:02d}_{variant_id}.png"
            out_path = os.path.join(out_dir, filename)
            generate_variant_card(image_path, pose, out_path, index=i)
            variants.append(
                {
                    "id": variant_id,
                    "image_url": f"/static/generated/{pet_id}/{filename}",
                    "pose_prompt": pose,
                    "path": out_path,  # server-side only (dropped from API response)
                }
            )
        return variants

    # -- Scene styling (used by the Flâneur comic pipeline later) -----------

    def tintinify_scene(self, image_path: str) -> str:
        """Restyle a street/scene image into Hergé ligne claire.

        Real implementation: ControlNet (lineart/depth) + Tintin LoRA pass.
            # workflow = build_tintinify_workflow(image_path)
            # requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})

        Stub: returns the input path unchanged.
        """
        return image_path

    def composite_pet_into_scene(
        self, scene_path: str, pet_path: str, position: tuple[int, int] | None = None
    ) -> str:
        """Composite a generated pet character into a styled scene.

        Real implementation will use a segmented pet cutout + depth-aware
        placement. Stub: returns the scene path unchanged (compositing happens
        in services/compositor.py once wired).
        """
        return scene_path
