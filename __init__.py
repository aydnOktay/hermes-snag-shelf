"""snag-shelf — everything that snagged, one Desktop shelf."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_DIR = str(Path(__file__).resolve().parent)
if _DIR in sys.path:
    sys.path.remove(_DIR)
sys.path.insert(0, _DIR)

import snag_context
import snag_hooks
import snag_schemas
import snag_tools


def _slash_text(raw: object) -> str:
    if not isinstance(raw, str):
        return str(raw)
    text = raw.strip()
    if not text.startswith("{"):
        return text
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return text
    if isinstance(data, dict):
        md = data.get("markdown")
        if isinstance(md, str) and md.strip():
            return md.strip()
        if data.get("ok") is False:
            return f"(error: {data.get('error') or 'failed'})"
    return text


def _handle_slash(ctx, raw_args: str) -> str:
    del ctx
    parts = (raw_args or "").strip().split()
    verb = (parts[0].lower() if parts else "list")
    if verb in {"help", "?"}:
        return (
            "Usage:\n"
            "  /snag              — snag list\n"
            "  /snag list         — same\n"
            "  /snag terminal     — terminal failures only\n"
            "  /snag file         — file-tool failures\n"
            "  /snag web          — web/browser failures\n"
            "  /snag clear        — clear unpinned items\n"
            "Open Snag Shelf in the sidebar for the full gallery."
        )
    if verb in {"clear", "reset"}:
        return _slash_text(
            snag_tools.snag_shelf_clear({"confirm": True, "keep_pinned": True})
        )
    kind = "all"
    if verb in {"terminal", "term", "shell"}:
        kind = "terminal"
    elif verb in {"file", "files"}:
        kind = "file"
    elif verb in {"web", "browser"}:
        kind = "web"
    elif verb in {"other"}:
        kind = "other"
    elif verb not in {"list", "show", "shelf", "snags"}:
        if verb in {"all", "terminal", "file", "web", "other"}:
            kind = verb
    return _slash_text(snag_tools.snag_shelf_list({"kind": kind, "markdown": True}))


def register(ctx) -> None:
    snag_context.set_ctx(ctx)
    ctx.register_tool(
        name="snag_shelf_list",
        toolset="snag_shelf",
        schema=snag_schemas.SNAG_SHELF_LIST,
        handler=snag_tools.snag_shelf_list,
    )
    ctx.register_tool(
        name="snag_shelf_clear",
        toolset="snag_shelf",
        schema=snag_schemas.SNAG_SHELF_CLEAR,
        handler=snag_tools.snag_shelf_clear,
    )
    ctx.register_hook("post_tool_call", snag_hooks.on_post_tool_call)

    try:
        ctx.register_command(
            "snag",
            handler=lambda raw: _handle_slash(ctx, raw),
            description="Snag Shelf — failed tool calls",
            args_hint="list|terminal|file|web|clear|help",
        )
    except TypeError:
        ctx.register_command(
            "snag",
            handler=lambda raw: _handle_slash(ctx, raw),
            description="Snag Shelf — failed tool calls",
        )

    skill_md = Path(__file__).parent / "skills" / "snag-shelf" / "SKILL.md"
    if skill_md.is_file():
        try:
            ctx.register_skill("snag-shelf", skill_md)
        except TypeError:
            ctx.register_skill("snag-shelf", str(skill_md))
