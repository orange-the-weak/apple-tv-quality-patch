"""Validated adapter entry point; incompatible input always fails closed."""
import hashlib
import json
from pathlib import Path
from .core import PatchError, validate_video_budget
from .adapters.v14_3_1 import patch_worker, patch_hls, patch_player

ADAPTER = json.loads((Path(__file__).parent / "adapters/apple_tv_14_3_1.json").read_text())
SUPPORTED_ASSETS = ADAPTER["assets"]

def verify_assets(assets):
    for name, expected in SUPPORTED_ASSETS.items():
        if name not in assets.namelist():
            raise PatchError("Missing asset: " + name)
        if hashlib.sha256(assets.read(name)).hexdigest() != expected:
            raise PatchError("Unsupported or already patched asset: " + name)

def patch_assets(assets, *, prefetch=True, reclaim_video=True, video_buffer_mib=0):
    validate_video_budget(video_buffer_mib)
    verify_assets(assets)
    return {
        "app-worker.chunk.js": patch_worker(assets.read("app-worker.chunk.js"), reclaim_video=reclaim_video, video_buffer_mib=video_buffer_mib),
        "hls-adopted.chunk.js": patch_hls(assets.read("hls-adopted.chunk.js"), prefetch=prefetch),
        "PlayerPage.js": patch_player(assets.read("PlayerPage.js")),
    }
