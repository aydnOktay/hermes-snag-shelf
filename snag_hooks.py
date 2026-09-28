"""post_tool_call observer — record failed tool calls. Never raise."""

from __future__ import annotations

import snag_store


def on_post_tool_call(
    tool_name: str = "",
    args: dict | None = None,
    result: object = "",
    session_id: str = "",
    status: str = "",
    **kwargs,
) -> None:
    del kwargs
    try:
        snag_store.record_snag(
            tool_name=str(tool_name or ""),
            args=args if isinstance(args, dict) else {},
            result=result,
            session_id=str(session_id or ""),
            status=str(status or ""),
        )
    except Exception:
        return
