"""Cross-session shelf of failed tool calls under plugin-data."""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PLUGIN_ID = "snag-shelf"
MAX_ITEMS = 80

SECRET_KEYS = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|auth|credential|bearer)",
    re.I,
)

OWN_TOOLS = {"snag_shelf_list", "snag_shelf_clear"}

TERMINAL_TOOLS = {
    "terminal",
    "run_terminal",
    "run_command",
    "execute",
    "shell",
    "bash",
}
FILE_TOOLS = {
    "read_file",
    "write_file",
    "patch",
    "search_files",
    "list_dir",
    "delete_file",
}
WEB_TOOLS = {
    "web_search",
    "web_fetch",
    "browser",
    "browse_page",
    "open_url",
}


def data_dir() -> Path:
    try:
        from plugins.plugin_storage import plugin_data_dir  # type: ignore

        return plugin_data_dir(PLUGIN_ID)
    except Exception:
        home = Path(os.environ.get("HERMES_HOME") or (Path.home() / ".hermes"))
        path = home / "plugin-data" / PLUGIN_ID
        path.mkdir(parents=True, exist_ok=True)
        return path


def state_path() -> Path:
    return data_dir() / "shelf.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty() -> dict[str, Any]:
    return {"items": []}


def load_state() -> dict[str, Any]:
    path = state_path()
    if not path.is_file():
        return _empty()
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return _empty()
    if not isinstance(raw, dict):
        return _empty()
    if not isinstance(raw.get("items"), list):
        raw["items"] = []
    return raw


def save_state(state: dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def classify_tool(tool_name: str) -> str:
    name = (tool_name or "").lower()
    if name in TERMINAL_TOOLS or "terminal" in name or "shell" in name:
        return "terminal"
    if name in FILE_TOOLS or name.endswith("_file") or name == "patch":
        return "file"
    if name in WEB_TOOLS or name.startswith("web_") or "browser" in name:
        return "web"
    return "other"


def _redact_value(key: str, value: Any, depth: int = 0) -> Any:
    if depth > 3:
        return "…"
    if SECRET_KEYS.search(key or ""):
        return "[redacted]"
    if isinstance(value, str):
        text = value.replace("\n", " ").strip()
        if len(text) > 160:
            text = text[:157] + "…"
        return text
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, list):
        return [_redact_value(key, v, depth + 1) for v in value[:6]]
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for i, (k, v) in enumerate(value.items()):
            if i >= 8:
                out["…"] = f"+{len(value) - 8} more"
                break
            out[str(k)[:64]] = _redact_value(str(k), v, depth + 1)
        return out
    return str(value)[:120]


def summarize_args(args: dict | None) -> str:
    payload = args if isinstance(args, dict) else {}
    if not payload:
        return ""
    redacted = {str(k)[:64]: _redact_value(str(k), v) for k, v in list(payload.items())[:10]}
    try:
        text = json.dumps(redacted, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        text = str(redacted)
    text = text.replace("\n", " ").strip()
    return text[:320]


def extract_error(result: object, status: str = "") -> str:
    if isinstance(result, dict):
        for key in ("error", "message", "detail", "stderr"):
            val = result.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip().replace("\n", " ")[:400]
        try:
            return json.dumps(result, ensure_ascii=False)[:400]
        except (TypeError, ValueError):
            return str(result)[:400]
    text = str(result or "").strip()
    if not text and status:
        return f"(status: {status})"
    # Prefer JSON error field when present
    if text.startswith("{") or text.startswith("["):
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            data = None
        if isinstance(data, dict):
            for key in ("error", "message", "detail", "stderr"):
                val = data.get(key)
                if isinstance(val, str) and val.strip():
                    return val.strip().replace("\n", " ")[:400]
            if data.get("ok") is False:
                return str(data.get("error") or data)[:400]
    return text.replace("\n", " ")[:400]


def looks_like_failure(status: str, result: object) -> bool:
    st = (status or "").strip().lower()
    if st in {"error", "failed", "failure", "blocked", "denied", "timeout", "cancelled", "canceled"}:
        return True
    if isinstance(result, dict):
        if result.get("ok") is False:
            return True
        err = result.get("error")
        if isinstance(err, str) and err.strip():
            return True
        return False
    text = str(result or "").strip()
    if not text:
        return bool(st) and st not in {"ok", "success", "succeeded", "completed"}
    low = text.lower()
    if low.startswith('{"ok": false') or low.startswith('{"ok":false'):
        return True
    try:
        data = json.loads(text)
        if isinstance(data, dict) and data.get("ok") is False:
            return True
        if isinstance(data, dict) and isinstance(data.get("error"), str) and data["error"].strip():
            return True
    except json.JSONDecodeError:
        pass
    needles = (
        "traceback (most recent call last)",
        "exception:",
        "error:",
        "failed:",
        "permission denied",
        "not found",
        "timed out",
        "timeout",
        "command not found",
        "enoent",
        "eacces",
    )
    return any(n in low for n in needles)


def fix_prompt(item: dict[str, Any]) -> str:
    tool = item.get("tool") or "?"
    kind = item.get("kind") or "other"
    status = item.get("status") or "error"
    args = item.get("args_summary") or "(none)"
    err = item.get("error") or "(no message)"
    return (
        "Please fix this Hermes tool failure:\n\n"
        f"Tool: `{tool}` ({kind})\n"
        f"Status: {status}\n"
        f"Args: {args}\n"
        f"Error: {err}\n\n"
        "What went wrong and how should we recover?"
    )


def record_snag(
    *,
    tool_name: str,
    args: dict | None = None,
    result: object = "",
    session_id: str = "",
    status: str = "",
) -> dict[str, Any] | None:
    name = str(tool_name or "").strip()
    if not name or name in OWN_TOOLS:
        return None
    if not looks_like_failure(status, result):
        return None
    kind = classify_tool(name)
    error = extract_error(result, status=status)
    if not error:
        error = f"(status: {status or 'error'})"
    args_summary = summarize_args(args if isinstance(args, dict) else {})
    entry = {
        "id": str(uuid.uuid4()),
        "at": now_iso(),
        "kind": kind,
        "tool": name[:64],
        "status": str(status or "error")[:64],
        "args_summary": args_summary,
        "error": error,
        "session_id": str(session_id or "")[:200],
        "pinned": False,
    }
    state = load_state()
    items: list[dict[str, Any]] = [it for it in state.get("items", []) if isinstance(it, dict)]
    items.append(entry)
    if len(items) > MAX_ITEMS:
        pinned_items = [it for it in items if it.get("pinned")]
        plain = [it for it in items if not it.get("pinned")]
        plain = plain[-(MAX_ITEMS - len(pinned_items)) :]
        items = pinned_items + plain
        items.sort(key=lambda it: str(it.get("at") or ""))
    state["items"] = items
    save_state(state)
    return entry


def list_items(*, kind: str | None = None, pinned_only: bool = False) -> list[dict[str, Any]]:
    items = [it for it in load_state().get("items", []) if isinstance(it, dict) and it.get("tool")]
    if kind and kind != "all":
        items = [it for it in items if it.get("kind") == kind]
    if pinned_only:
        items = [it for it in items if it.get("pinned")]
    return items


def set_pinned(item_id: str, pinned: bool) -> bool:
    state = load_state()
    items = [it for it in state.get("items", []) if isinstance(it, dict)]
    found = False
    for it in items:
        if it.get("id") == item_id:
            it["pinned"] = bool(pinned)
            found = True
            break
    if not found:
        return False
    state["items"] = items
    save_state(state)
    return True


def remove_item(item_id: str) -> bool:
    state = load_state()
    items = [it for it in state.get("items", []) if isinstance(it, dict)]
    next_items = [it for it in items if it.get("id") != item_id]
    if len(next_items) == len(items):
        return False
    state["items"] = next_items
    save_state(state)
    return True


def clear_items(*, keep_pinned: bool = True) -> int:
    state = load_state()
    items = [it for it in state.get("items", []) if isinstance(it, dict)]
    if keep_pinned:
        kept = [it for it in items if it.get("pinned")]
        n = len(items) - len(kept)
        state["items"] = kept
    else:
        n = len(items)
        state["items"] = []
    save_state(state)
    return n


def snapshot(kind: str | None = None) -> dict[str, Any]:
    items = list_items(kind=kind)
    pinned = [it for it in items if it.get("pinned")]
    return {
        "ok": True,
        "count": len(items),
        "pinned_count": len(pinned),
        "items": items,
    }


def to_markdown(items: list[dict[str, Any]] | None = None) -> str:
    rows = items if items is not None else list_items()
    if not rows:
        return "(Snag Shelf is empty)"
    lines = [f"Snag Shelf — {len(rows)} failures"]
    for i, it in enumerate(reversed(rows), 1):
        pin = "★ " if it.get("pinned") else ""
        err = (it.get("error") or "")[:120]
        lines.append(
            f"{i}. {pin}`{it.get('tool')}` ({it.get('kind')}) — {err}"
        )
    return "\n".join(lines)
