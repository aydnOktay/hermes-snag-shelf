"""Tool handlers — always return JSON strings, never raise."""

from __future__ import annotations

import json

import snag_store


def snag_shelf_list(args: dict, **kwargs) -> str:
    del kwargs
    try:
        payload = args if isinstance(args, dict) else {}
        kind = str(payload.get("kind") or "all")
        snap = snag_store.snapshot(kind=None if kind == "all" else kind)
        if payload.get("markdown") is not False:
            snap["markdown"] = snag_store.to_markdown(snap.get("items") or [])
        return json.dumps(snap, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})


def snag_shelf_clear(args: dict, **kwargs) -> str:
    del kwargs
    try:
        payload = args if isinstance(args, dict) else {}
        if payload.get("confirm") is not True:
            return json.dumps(
                {"ok": False, "error": "pass confirm=true to clear the shelf"}
            )
        keep = payload.get("keep_pinned")
        keep_pinned = True if keep is None else bool(keep)
        n = snag_store.clear_items(keep_pinned=keep_pinned)
        snap = snag_store.snapshot()
        snap["cleared"] = n
        return json.dumps(snap, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"ok": False, "error": str(exc)})
