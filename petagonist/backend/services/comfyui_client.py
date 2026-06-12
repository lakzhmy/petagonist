"""ComfyUI client — Seam 1 (generate_pet_variants) is live.

Seams 2 & 3 (tintinify_scene, composite_pet_into_scene) are still stubbed.
When ComfyUI is unreachable or the pet has no photo, every method falls back
to Pillow placeholders so the app always renders.
"""

from __future__ import annotations

import copy
import json
import logging
import os
import time
import uuid

import requests

from .placeholders import generate_variant_card

log = logging.getLogger(__name__)

COMFYUI_URL = os.environ.get("COMFYUI_URL", "http://localhost:8188")

STYLE_PREFIX = (
    "PETAGONIST.2, comic style, small black dot eyes, one line eyebrows, "
    "simplified details, paper texture, bright colors, "
    "quadruped, four legs, animal anatomy, pet in photo "
)

_STRIP_NODES = {
    "1153", "1154",
    "1101:758", "1101:759", "1101:760",
    "1101:762",
    "1101:847", "1101:848", "1101:849", "1101:853", "1101:854",
}

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKFLOW_PATH = os.path.join(_BACKEND_DIR, "workflows", "generate_pet_variants.json")


def _load_workflow() -> dict:
    with open(_WORKFLOW_PATH, encoding="utf-8") as f:
        wf = json.load(f)
    for node_id in _STRIP_NODES:
        wf.pop(node_id, None)
    wf["1198"]["inputs"]["string_a"] = ""
    return wf


_BASE_WORKFLOW = _load_workflow()


class ComfyUIClient:
    """Thin wrapper around the ComfyUI REST API."""

    def __init__(self, generated_root: str):
        self.generated_root = generated_root

    def _is_available(self) -> bool:
        try:
            r = requests.get(f"{COMFYUI_URL}/system_stats", timeout=2)
            return r.status_code == 200
        except Exception:
            return False

    def _upload_image(self, image_path: str) -> str:
        """Upload an image to ComfyUI's input folder. Returns the filename."""
        with open(image_path, "rb") as f:
            r = requests.post(
                f"{COMFYUI_URL}/upload/image",
                files={"image": (os.path.basename(image_path), f, "image/png")},
                data={"overwrite": "true"},
            )
        r.raise_for_status()
        return r.json()["name"]

    def _submit_and_wait(self, workflow: dict, timeout: float = 120) -> dict:
        """POST a workflow prompt, poll until done, return the history entry."""
        r = requests.post(f"{COMFYUI_URL}/prompt", json={"prompt": workflow})
        r.raise_for_status()
        prompt_id = r.json()["prompt_id"]

        deadline = time.time() + timeout
        while time.time() < deadline:
            time.sleep(1.5)
            hist = requests.get(f"{COMFYUI_URL}/history/{prompt_id}").json()
            if prompt_id in hist:
                return hist[prompt_id]
        raise TimeoutError(f"ComfyUI prompt {prompt_id} did not finish in {timeout}s")

    def _download_output(self, image_info: dict, save_path: str) -> None:
        """Download a generated image from ComfyUI and save it locally."""
        r = requests.get(
            f"{COMFYUI_URL}/view",
            params={
                "filename": image_info["filename"],
                "subfolder": image_info.get("subfolder", ""),
                "type": image_info.get("type", "output"),
            },
        )
        r.raise_for_status()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        with open(save_path, "wb") as f:
            f.write(r.content)

    # -- Seam 1: pet → character variants ------------------------------------

    def generate_pet_variants(
        self,
        image_path: str | None,
        description: str,
        pose_prompts: list[str],
        pet_id: str,
    ) -> list[dict]:
        if image_path is None:
            log.info("No pet photo — using placeholders")
            return self._placeholder_variants(image_path, pose_prompts, pet_id)

        if not self._is_available():
            log.warning("ComfyUI not reachable at %s — using placeholders", COMFYUI_URL)
            return self._placeholder_variants(image_path, pose_prompts, pet_id)

        try:
            comfy_filename = self._upload_image(image_path)
        except Exception:
            log.exception("Failed to upload image to ComfyUI")
            return self._placeholder_variants(image_path, pose_prompts, pet_id)

        out_dir = os.path.join(self.generated_root, pet_id)
        variants: list[dict] = []

        for i, pose in enumerate(pose_prompts):
            variant_id = uuid.uuid4().hex[:8]
            filename = f"variant_{i:02d}_{variant_id}.png"
            out_path = os.path.join(out_dir, filename)

            try:
                wf = copy.deepcopy(_BASE_WORKFLOW)
                wf["1097"]["inputs"]["image"] = comfy_filename
                wf["1198"]["inputs"]["string_a"] = STYLE_PREFIX + pose
                wf["1159"]["inputs"]["value"] = (hash(pet_id) + i) % (2**31)
                wf["1102"]["inputs"]["filename_prefix"] = f"petagonist/{pet_id}/variant_{i:02d}"

                history = self._submit_and_wait(wf)
                images = history["outputs"]["1102"]["images"]
                self._download_output(images[0], out_path)
                log.info("Variant %d/%d done: %s", i + 1, len(pose_prompts), pose[:40])
            except Exception:
                log.exception("ComfyUI failed for variant %d — falling back to placeholder", i)
                generate_variant_card(image_path, pose, out_path, index=i)

            variants.append(
                {
                    "id": variant_id,
                    "image_url": f"/static/generated/{pet_id}/{filename}",
                    "pose_prompt": pose,
                    "path": out_path,
                }
            )

        return variants

    def _placeholder_variants(
        self, image_path: str | None, pose_prompts: list[str], pet_id: str
    ) -> list[dict]:
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
                    "path": out_path,
                }
            )
        return variants

    # -- Seam 2: scene styling (still stubbed) --------------------------------

    def tintinify_scene(self, image_path: str) -> str:
        return image_path

    # -- Seam 3: compositing (still stubbed) ----------------------------------

    def composite_pet_into_scene(
        self, scene_path: str, pet_path: str, position: tuple[int, int] | None = None
    ) -> str:
        return scene_path
