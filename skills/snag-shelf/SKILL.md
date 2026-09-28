---
name: snag-shelf
description: >
  Use when the user asks about recent tool failures, what snagged, or wants
  the Snag Shelf gallery. Load with skill_view("snag-shelf:snag-shelf").
---

# snag-shelf

Cross-session shelf of failed tool calls (status / ok:false / error text).
Redacted args + error snippets only — no secrets uploaded. Prefer pointing
the user at the Snag Shelf Desktop page.

## Notes

- Clear removes shelf entries only
- Pin keeps items across clear
- Insert fix prompt uses host.composer.insertText (Hermes >= 0.21.5)
