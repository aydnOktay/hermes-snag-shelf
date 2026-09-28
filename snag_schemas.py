"""JSON tool schemas."""

from __future__ import annotations

SNAG_SHELF_LIST = {
    "name": "snag_shelf_list",
    "description": (
        "List failed Hermes tool calls on the Snag Shelf — cross-session "
        "gallery of errors (tool, redacted args, error snippet). Metadata only."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "kind": {
                "type": "string",
                "enum": ["all", "terminal", "file", "web", "other"],
                "description": "Filter by kind (default all).",
            },
            "markdown": {"type": "boolean"},
        },
        "additionalProperties": False,
    },
}

SNAG_SHELF_CLEAR = {
    "name": "snag_shelf_clear",
    "description": (
        "Clear Snag Shelf items locally. By default keeps pinned entries. "
        "Does not change anything outside plugin-data."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "confirm": {"type": "boolean"},
            "keep_pinned": {"type": "boolean", "default": True},
        },
        "required": ["confirm"],
        "additionalProperties": False,
    },
}
