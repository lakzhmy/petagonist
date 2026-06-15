"""ComfyUI client — Seams 1 & 2+3 are live.

Seam 1: generate_pet_variants (pet photo → comic character variants).
Seam 2+3 combined: composite_panel (pet variant + scene photo → final comic panel).

When ComfyUI is unreachable, every method falls back to Pillow placeholders.
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

# -- Seam 1 constants --------------------------------------------------------

STYLE_PREFIX = (
    "PETAGONIST.2, comic style, small black dot eyes, one line eyebrows, "
    "simplified details, paper texture, bright colors, "
    "quadruped, four legs, animal anatomy, pet in photo "
)

_VARIANT_STRIP_NODES = {
    "1153", "1154",
    "1101:758", "1101:759", "1101:760",
    "1101:762",
    "1101:847", "1101:848", "1101:849", "1101:853", "1101:854",
}

# -- Seam 2+3 constants ------------------------------------------------------

PANEL_PROMPT = (
    "comic style, tintin comic style, flat color, paper texture, "
    "Place the pet in Image 1 onto Image 2. "
    "Image 2 should be in tintin comic style. "
    "The pet in Image 1 is doing an action. "
    "small pet, pet is smaller than people, correct animal proportions, "
    "pet on the ground, natural scale"
)

PANEL_NEGATIVE = (
    "PETAGONIST, petagonist, Petagonist, text, words, letters, writing, "
    "watermark, signature, logo, title, signage, banner, sign, "
    "speech bubble, comic bubble, dialogue box, caption, "
    "multiple pets, duplicate pet, extra animals, "
    "extra limbs, extra legs, extra arms, multiple heads, extra head, "
    "giant animal, oversized pet, huge pet, pet larger than human, "
    "deformed, mutated, disfigured, malformed"
)

_PANEL_STRIP_NODES = {
    "1236:1179", "1236:1180", "1236:1181",
    "1236:1183",
    "1236:1188", "1236:1189", "1236:1190", "1236:1191", "1236:1192",
}

# -- Load workflow templates --------------------------------------------------

_BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORKFLOWS_DIR = os.path.join(_BACKEND_DIR, "workflows")


def _load_workflow(filename: str, strip: set[str], patches: dict | None = None) -> dict:
    with open(os.path.join(_WORKFLOWS_DIR, filename), encoding="utf-8") as f:
        wf = json.load(f)
    for node_id in strip:
        wf.pop(node_id, None)
    if patches:
        for node_id, field_patches in patches.items():
            if node_id in wf:
                for key, val in field_patches.items():
                    wf[node_id]["inputs"][key] = val
    return wf


_VARIANT_WF = _load_workflow(
    "generate_pet_variants.json",
    _VARIANT_STRIP_NODES,
    {"1198": {"string_a": ""}},
)

_PANEL_WF = _load_workflow(
    "composite_pet_into_scene.json",
    _PANEL_STRIP_NODES,
    {
        "1236:1186": {"prompt": PANEL_NEGATIVE},
        "1236:1185": {"value": 3.5},
    },
)


# -- Client -------------------------------------------------------------------

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

    def _submit_and_wait(self, workflow: dict, timeout: float = 300) -> dict:
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

    def prepare_comfyui(self, image_path: str | None) -> str | None:
        """Upload the pet image once. Returns ComfyUI filename, or None on failure."""
        if image_path is None:
            return None
        if not self._is_available():
            log.warning("ComfyUI not reachable at %s", COMFYUI_URL)
            return None
        try:
            return self._upload_image(image_path)
        except Exception:
            log.exception("Failed to upload image to ComfyUI")
            return None

    # -- Seam 1: pet → character variants ------------------------------------

    def generate_single_variant(
        self,
        image_path: str | None,
        description: str,
        pose: str,
        pet_id: str,
        index: int = 0,
        comfy_filename: str | None = None,
    ) -> dict:
        """Generate one variant. Falls back to placeholder on any failure."""
        variant_id = uuid.uuid4().hex[:8]
        filename = f"variant_{index:02d}_{variant_id}.png"
        out_dir = os.path.join(self.generated_root, pet_id)
        out_path = os.path.join(out_dir, filename)

        if comfy_filename:
            try:
                wf = copy.deepcopy(_VARIANT_WF)
                wf["1097"]["inputs"]["image"] = comfy_filename
                desc_part = f"{description}, " if description else ""
                wf["1198"]["inputs"]["string_a"] = STYLE_PREFIX + desc_part + pose
                wf["1159"]["inputs"]["value"] = (hash(pet_id) + index) % (2**31)
                wf["1102"]["inputs"]["filename_prefix"] = (
                    f"petagonist/{pet_id}/variant_{index:02d}"
                )
                history = self._submit_and_wait(wf)
                images = history["outputs"]["1102"]["images"]
                self._download_output(images[0], out_path)
                log.info("Variant %d done: %s", index, pose[:40])
            except Exception:
                log.exception("ComfyUI failed for variant %d — placeholder fallback", index)
                generate_variant_card(image_path, pose, out_path, index=index)
        else:
            generate_variant_card(image_path, pose, out_path, index=index)

        return {
            "id": variant_id,
            "image_url": f"/static/generated/{pet_id}/{filename}",
            "pose_prompt": pose,
            "path": out_path,
        }

    def generate_pet_variants(
        self,
        image_path: str | None,
        description: str,
        pose_prompts: list[str],
        pet_id: str,
    ) -> list[dict]:
        """Batch helper — generates all variants sequentially."""
        comfy_filename = self.prepare_comfyui(image_path)
        return [
            self.generate_single_variant(
                image_path, description, pose, pet_id, i, comfy_filename
            )
            for i, pose in enumerate(pose_prompts)
        ]

    # -- Seam 2+3 combined: scene + pet → final panel ------------------------

    def composite_panel(
        self,
        scene_path: str,
        pet_variant_path: str,
        out_path: str,
        seed: int = 0,
    ) -> str:
        """Tintinify a scene and composite the pet into it in one ComfyUI pass.

        Falls back to returning scene_path unchanged if ComfyUI is down.
        """
        if not self._is_available():
            log.warning("ComfyUI not reachable — skipping panel compositing")
            return scene_path

        try:
            scene_comfy = self._upload_image(scene_path)
            pet_comfy = self._upload_image(pet_variant_path)
        except Exception:
            log.exception("Failed to upload images for panel compositing")
            return scene_path

        try:
            wf = copy.deepcopy(_PANEL_WF)
            wf["1213"]["inputs"]["image"] = pet_comfy
            wf["1215"]["inputs"]["image"] = scene_comfy
            wf["1214"]["inputs"]["value"] = PANEL_PROMPT
            wf["1236:1175"]["inputs"]["value"] = seed % (2**31)
            wf["1211"]["inputs"]["filename_prefix"] = (
                f"petagonist/panels/{os.path.basename(out_path).replace('.png', '')}"
            )

            history = self._submit_and_wait(wf, timeout=300)
            images = history["outputs"]["1211"]["images"]
            self._download_output(images[0], out_path)
            log.info("Panel composited: %s", os.path.basename(out_path))
            return out_path
        except Exception:
            log.exception("ComfyUI panel compositing failed — using raw scene")
            return scene_path

    # -- Legacy stubs (kept for backwards compat) -----------------------------

    def tintinify_scene(self, image_path: str) -> str:
        return image_path

    def composite_pet_into_scene(
        self, scene_path: str, pet_path: str, position: tuple[int, int] | None = None,
    ) -> str:
        return scene_path
