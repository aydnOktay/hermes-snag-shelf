"""Dashboard/Desktop backend — /api/plugins/snag-shelf/."""

from __future__ import annotations

import sys
from pathlib import Path

from fastapi import APIRouter, Request

_ROOT = Path(__file__).resolve().parent.parent
_root_str = str(_ROOT)
if _root_str in sys.path:
    sys.path.remove(_root_str)
sys.path.insert(0, _root_str)

import snag_store  # noqa: E402

router = APIRouter()


def _payload(request_json: object) -> dict:
    if isinstance(request_json, dict):
        return request_json
    return {}


@router.get("/shelf")
async def shelf(kind: str = "all") -> dict:
    k = None if kind in {"", "all"} else kind
    return snag_store.snapshot(kind=k)


@router.post("/pin")
async def pin(request: Request) -> dict:
    try:
        body = _payload(await request.json())
    except Exception:
        body = {}
    item_id = str(body.get("id") or "").strip()
    if not item_id:
        return {"ok": False, "error": "id is required"}
    pinned = body.get("pinned")
    ok = snag_store.set_pinned(item_id, True if pinned is None else bool(pinned))
    snap = snag_store.snapshot()
    snap["ok"] = ok
    if not ok:
        snap["error"] = "not found"
    return snap


@router.post("/remove")
async def remove(request: Request) -> dict:
    try:
        body = _payload(await request.json())
    except Exception:
        body = {}
    item_id = str(body.get("id") or "").strip()
    if not item_id:
        return {"ok": False, "error": "id is required"}
    ok = snag_store.remove_item(item_id)
    snap = snag_store.snapshot()
    snap["ok"] = ok
    if not ok:
        snap["error"] = "not found"
    return snap


@router.post("/clear")
async def clear(request: Request) -> dict:
    try:
        body = _payload(await request.json())
    except Exception:
        body = {}
    keep = body.get("keep_pinned")
    keep_pinned = True if keep is None else bool(keep)
    n = snag_store.clear_items(keep_pinned=keep_pinned)
    snap = snag_store.snapshot()
    snap["cleared"] = n
    return snap


@router.get("/fix-prompt")
async def fix_prompt(id: str = "") -> dict:
    item_id = (id or "").strip()
    if not item_id:
        return {"ok": False, "error": "id is required"}
    for it in snag_store.list_items():
        if it.get("id") == item_id:
            return {"ok": True, "text": snag_store.fix_prompt(it), "item": it}
    return {"ok": False, "error": "not found"}
