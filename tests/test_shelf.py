"""Local checks — no Hermes / network required."""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["HERMES_HOME"] = tempfile.mkdtemp(prefix="snag-shelf-test-")

import snag_hooks
import snag_store
import snag_tools


def test_detect_and_record() -> None:
    assert snag_store.looks_like_failure("error", "boom")
    assert snag_store.looks_like_failure("", '{"ok": false, "error": "nope"}')
    assert not snag_store.looks_like_failure("ok", "wrote 12 lines")
    assert not snag_store.looks_like_failure("ok", {"ok": True})

    entry = snag_store.record_snag(
        tool_name="write_file",
        args={"path": "C:/tmp/x.py", "token": "secret-value"},
        result='{"ok": false, "error": "permission denied"}',
        session_id="s1",
        status="error",
    )
    assert entry and entry["kind"] == "file"
    assert "permission denied" in entry["error"]
    assert "[redacted]" in entry["args_summary"]
    assert "secret-value" not in entry["args_summary"]

    term = snag_store.record_snag(
        tool_name="terminal",
        args={"command": "ls missing"},
        result="ls: missing: No such file",
        status="failed",
    )
    assert term and term["kind"] == "terminal"

    web = snag_store.record_snag(
        tool_name="web_search",
        args={"query": "x"},
        result="Error: timed out",
        status="",
    )
    assert web and web["kind"] == "web"


def test_hooks_skip_success() -> None:
    snag_store.clear_items(keep_pinned=False)
    snag_hooks.on_post_tool_call(
        tool_name="write_file",
        args={"path": "/ok.py"},
        result="wrote 3 lines",
        session_id="abc",
        status="ok",
    )
    assert snag_store.list_items() == []
    snag_hooks.on_post_tool_call(
        tool_name="patch",
        args={"path": "/bad.py"},
        result='{"ok": false, "error": "hunk failed"}',
        session_id="abc",
        status="error",
    )
    items = snag_store.list_items()
    assert len(items) == 1
    assert items[0]["tool"] == "patch"


def test_pin_tools_and_prompt() -> None:
    snag_store.clear_items(keep_pinned=False)
    e = snag_store.record_snag(
        tool_name="shell",
        args={"command": "false"},
        result="exit 1",
        status="failed",
    )
    assert e
    prompt = snag_store.fix_prompt(e)
    assert "shell" in prompt and "exit 1" in prompt
    assert snag_store.set_pinned(e["id"], True)
    data = json.loads(snag_tools.snag_shelf_list({"markdown": True}))
    assert data["ok"] is True
    assert data["count"] >= 1
    cleared = json.loads(
        snag_tools.snag_shelf_clear({"confirm": True, "keep_pinned": True})
    )
    assert cleared["ok"] is True
    assert cleared["count"] >= 1


if __name__ == "__main__":
    test_detect_and_record()
    test_hooks_skip_success()
    test_pin_tools_and_prompt()
    print("ok")
